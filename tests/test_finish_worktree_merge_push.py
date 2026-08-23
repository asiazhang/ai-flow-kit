"""finish-worktree/merge-push.sh：同步主干、--no-ff 合并并推送。"""

from pathlib import Path

from conftest import SKILLS, commit_in, git, kv, out, run_script, section

SCRIPT = "finish-worktree/scripts/merge-push.sh"


def run_merge_push(cwd):
    return run_script(SKILLS / SCRIPT, cwd)


def remote_main_hash(repo) -> str:
    return git("ls-remote", str(repo.remote), "refs/heads/main").stdout.split()[0]


def clone_at(repo, name: str) -> Path:
    """克隆远程到 repo.root/<name> 并配置身份，返回路径。"""
    path = repo.root / name
    git("clone", str(repo.remote), str(path))
    git("config", "user.name", "Test User", cwd=path)
    git("config", "user.email", "test@example.com", cwd=path)
    return path


def install_reject_hook(repo, reject_times: int) -> Path:
    """安装 pre-push hook：前 reject_times 次 push 前向远程注入新提交。

    注入通过另一个 clone（injector）完成，是真实的远程变化，使原 push 非快进被拒。
    """
    injector = clone_at(repo, "injector")

    git_dir = Path(repo.git("rev-parse", "--absolute-git-dir").stdout.strip())
    hook = git_dir / "hooks" / "pre-push"
    count_file = repo.root / "reject-count"
    hook.write_text(
        f"""#!/bin/sh
set -e
count_file={count_file}
injector={injector}
times={reject_times}
if [ -f "$count_file" ]; then
  n=$(cat "$count_file")
else
  n=0
fi
n=$((n + 1))
echo "$n" > "$count_file"
if [ "$n" -le "$times" ]; then
  cd "$injector"
  git pull -q origin main --ff-only
  echo "inject $n" >> inject.txt
  git add -A
  git commit -qm "chore: inject $n"
  git push -q origin main
fi
exit 0
"""
    )
    hook.chmod(0o755)
    return injector


def test_merge_push_no_ff_and_push(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")

    p = run_merge_push(wt)
    assert p.returncode == 0, out(p)
    merge_commit = kv(p.stdout, "MERGE_COMMIT")
    assert merge_commit
    assert kv(p.stdout, "PUSHED") == "true"
    assert kv(p.stdout, "SYNCED") == "false"
    assert kv(p.stdout, "ALREADY_MERGED") == "false"

    # 远程 main 指向合并提交（已推送）
    assert remote_main_hash(repo) == merge_commit

    # 合并为 --no-ff：merge commit 有两个 parent
    parents = git("rev-list", "--parents", "-n", "1", merge_commit, cwd=repo.work)
    assert len(parents.stdout.split()) == 3

    # dev 分支仍保留
    assert git("rev-parse", "-q", "--verify", "refs/heads/dev/feature", cwd=repo.work).returncode == 0


def test_merge_push_sync_main_first(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")

    # 远程 main 出现新提交（本地 main 落后）
    ahead = clone_at(repo, "ahead")
    (ahead / "remote.txt").write_text("remote change\n")
    git("add", "-A", cwd=ahead)
    git("commit", "-qm", "chore: remote change", cwd=ahead)
    git("push", "-q", "origin", "main", cwd=ahead)

    p = run_merge_push(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "SYNCED") == "true"
    assert kv(p.stdout, "PUSHED") == "true"

    # 远程 main 同时包含远程新提交与 dev 提交
    history = git("log", "--oneline", remote_main_hash(repo), cwd=repo.work).stdout
    assert "remote change" in history
    assert "feat: feature" in history


def test_merge_push_reject_retry_once(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    install_reject_hook(repo, reject_times=1)

    p = run_merge_push(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "PUSHED") == "true"
    assert kv(p.stdout, "SYNCED") == "true"

    # 远程 main 包含注入提交与 dev 提交
    history = git("log", "--oneline", remote_main_hash(repo), cwd=repo.work).stdout
    assert "inject 1" in history
    assert "feat: feature" in history


def test_merge_push_reject_then_stop(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    injector = install_reject_hook(repo, reject_times=2)

    p = run_merge_push(wt)
    assert p.returncode == 1, out(p)
    assert "重试推送仍被拒绝" in p.stderr

    # 远程 main 停在注入器最后一次推送（inject 2），dev 提交未被推送
    assert remote_main_hash(repo) == git("rev-parse", "HEAD", cwd=injector).stdout.strip()


def test_merge_push_already_merged_skips_merge(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    repo.git("merge", "--no-ff", "dev/feature", "-m", "merge: dev/feature")
    repo.git("push", "-q", "origin", "main")
    before = git("rev-list", "--count", "main", cwd=repo.work).stdout.strip()

    p = run_merge_push(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "ALREADY_MERGED") == "true"
    assert kv(p.stdout, "MERGE_COMMIT") == ""  # 不创建空合并提交
    assert kv(p.stdout, "PUSHED") == "true"

    # 主干提交数不变（未产生新提交）
    after = git("rev-list", "--count", "main", cwd=repo.work).stdout.strip()
    assert after == before


def test_merge_push_conflict_stops(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")

    (repo.work / "conf.txt").write_text("main version\n")
    repo.git("add", "-A")
    repo.git("commit", "-qm", "chore: main change")

    (wt / "conf.txt").write_text("dev version\n")
    git("add", "-A", cwd=wt)
    git("commit", "-qm", "feat: dev change", cwd=wt)

    p = run_merge_push(wt)
    assert p.returncode == 1, out(p)
    assert kv(p.stdout, "CONFLICTED") == "true"
    assert "conf.txt" in section(p.stdout, "CONFLICT_FILES")

    # 冲突未自动解决，工作区仍处于冲突状态
    assert "conf.txt" in git("status", "--porcelain", cwd=repo.work).stdout
    # dev 提交未推送
    assert remote_main_hash(repo) != git("rev-parse", "HEAD", cwd=wt).stdout.strip()


def test_merge_push_main_worktree_dirty_stops(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    (repo.work / "wip.txt").write_text("wip\n")

    p = run_merge_push(wt)
    assert p.returncode == 1, out(p)
    assert "commit-and-push" in p.stderr


def test_merge_push_in_main_worktree_stops(repo_factory):
    repo = repo_factory()
    p = run_merge_push(repo.work)
    assert p.returncode == 1, out(p)
    assert "dev worktree" in p.stderr
