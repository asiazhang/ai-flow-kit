"""finish-worktree 端到端：单次测试调用完整走通收尾流程（合并 → 关 issue → 清理 → 报告）。

按 SKILL.md 的调用约定，在同一 dev worktree 内依次运行 Preflight / Identify / Merge /
Close / Cleanup 各脚本（模拟模型执行完整收尾），并断言最终报告六要素与真实仓库状态一致。
"""

import os
import subprocess

from conftest import SKILLS, commit_in, git, kv, out, run_script, section

SCRIPTS = SKILLS / "finish-worktree" / "scripts"
GITHUB_ORIGIN = "git@github.com:asiazhang/ai-flow-kit.git"
ISSUE = 42


def install_fake_gh(repo, *, state="OPEN") -> tuple:
    """安装 fake-gh 桩：记录每次调用参数（>>> 行），issue view 返回给定状态。"""
    fake_dir = repo.root / "fake-gh"
    fake_dir.mkdir(exist_ok=True)
    log = fake_dir / "calls.log"
    gh = fake_dir / "gh"
    gh.write_text(
        f"""#!/bin/sh
printf '>>> %s\\n' "$*" >> {log}
case "$1" in
  issue)
    case "$2" in
      view) printf '%s\\n' '{state}' ;;
    esac
    ;;
esac
exit 0
"""
    )
    gh.chmod(0o755)
    return gh, log


def calls(log) -> list[str]:
    """fake-gh 收到的调用参数行（>>> 前缀）；未调用时返回空列表。"""
    if not log.exists():
        return []
    return [line[4:] for line in log.read_text().splitlines() if line.startswith(">>> ")]


def run_close_issue(cwd, issue, *, gh_bin, merge_commit) -> subprocess.CompletedProcess:
    """以 GH_BIN / MERGE_COMMIT 环境变量运行 close-issue.sh（与 SKILL.md 步骤 4 一致）。"""
    env = os.environ.copy()
    env["GH_BIN"] = str(gh_bin)
    env["MERGE_COMMIT"] = merge_commit
    return subprocess.run(
        ["bash", str(SCRIPTS / "close-issue.sh"), str(issue)],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def push_dev_branch(wt, branch: str) -> None:
    git("push", "-q", "-u", "origin", branch, cwd=wt)


def worktree_list(repo) -> str:
    return git("worktree", "list", cwd=repo.work).stdout


def has_local_branch(repo, branch: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/heads/{branch}"],
        cwd=repo.work,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def remote_refs(repo) -> str:
    return git("ls-remote", str(repo.remote)).stdout


def remote_main_hash(repo) -> str:
    return git("ls-remote", str(repo.remote), "refs/heads/main").stdout.split()[0]


def test_full_flow_merge_close_cleanup_report(repo_factory):
    """完整收尾场景：单次测试调用走通 合并 → 关 issue → 清理 → 报告。"""
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, f"feat: 完成功能 (#{ISSUE})")
    push_dev_branch(wt, "dev/feature")  # 远程 dev 分支存在，清理时需删除
    gh, log = install_fake_gh(repo, state="OPEN")

    # 1. Preflight：识别 dev worktree、校验工作区已提交干净
    p = run_script(SCRIPTS / "preflight.sh", wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CURRENT_BRANCH") == "dev/feature"
    assert kv(p.stdout, "IS_MAIN_WORKTREE") == "false"
    assert kv(p.stdout, "WORKING_TREE_CLEAN") == "true"
    assert kv(p.stdout, "ALREADY_MERGED") == "false"

    # 2. Identify：从提交信息提取 issue 候选（单候选 → 确定为待关闭 issue）
    p = run_script(SCRIPTS / "extract-issue.sh", wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "ISSUE_COUNT") == "1"
    assert section(p.stdout, "CANDIDATES") == str(ISSUE)

    # 3. Merge：--no-ff 合并进 main 并推送
    merge_p = run_script(SCRIPTS / "merge-push.sh", wt)
    assert merge_p.returncode == 0, out(merge_p)
    merge_commit = kv(merge_p.stdout, "MERGE_COMMIT")
    assert merge_commit
    assert kv(merge_p.stdout, "PUSHED") == "true"

    # 4. Close：关闭关联 issue，评论注明合并提交哈希
    # （close-issue 从 origin 解析 owner/repo；fixture 的本地路径 origin 无法解析，
    #   真实仓库 origin 即为可解析的 GitHub URL，故仅在本步骤期间切换）
    repo.git("remote", "set-url", "origin", GITHUB_ORIGIN)
    close_p = run_close_issue(wt, ISSUE, gh_bin=gh, merge_commit=merge_commit)
    repo.git("remote", "set-url", "origin", str(repo.remote))
    assert close_p.returncode == 0, out(close_p)
    assert kv(close_p.stdout, "CLOSED") == "true"
    assert kv(close_p.stdout, "COMMENTED") == "true"
    assert kv(close_p.stdout, "REPO") == "asiazhang/ai-flow-kit"

    # 5. Cleanup：移除 worktree、删除本地/远程 dev 分支
    cleanup_p = run_script(SCRIPTS / "cleanup.sh", wt)
    assert cleanup_p.returncode == 0, out(cleanup_p)
    assert kv(cleanup_p.stdout, "WORKTREE_REMOVED") == "true"
    assert kv(cleanup_p.stdout, "LOCAL_BRANCH_DELETED") == "true"
    assert kv(cleanup_p.stdout, "REMOTE_BRANCH_DELETED") == "true"

    # 6. Report：最终报告六要素与真实仓库状态逐一对应
    #    （①合并提交 ②推送状态 ③issue 关闭结果 ④worktree 清理结果 ⑤分支清理结果 ⑥残留项）
    assert merge_commit == remote_main_hash(repo)  # ① 合并提交即远程 main HEAD
    assert kv(merge_p.stdout, "PUSHED") == "true"  # ② 推送状态
    close_calls = calls(log)
    assert close_calls[-1] == f"issue close {ISSUE} -R asiazhang/ai-flow-kit"  # ③ 已关闭
    assert merge_commit in close_calls[-2]  # ③ 关闭评论注明合并提交哈希
    assert str(wt) not in worktree_list(repo)  # ④ worktree 已移除
    assert not has_local_branch(repo, "dev/feature")  # ⑤ 本地分支已删除
    assert "refs/heads/dev/feature" not in remote_refs(repo)  # ⑤ 远程分支已删除
    assert section(cleanup_p.stdout, "REMAINING") == ""  # ⑥ 无残留


def test_full_flow_already_merged_skips_merge_and_close(repo_factory):
    """分支已合入主干：跳过合并（无新合并提交）→ 跳过 Close（无哈希可注明）→ 仍清理。

    对应 SKILL.md 步骤 3/4 的幂等分支：MERGE_COMMIT 为空时不执行 Close，
    宁可不关、不要关错；cleanup 照常执行。
    """
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, f"feat: 完成功能 (#{ISSUE})")
    push_dev_branch(wt, "dev/feature")
    repo.git("merge", "--no-ff", "dev/feature", "-m", "merge: dev/feature")
    repo.git("push", "-q", "origin", "main")
    gh, log = install_fake_gh(repo, state="OPEN")

    p = run_script(SCRIPTS / "preflight.sh", wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "ALREADY_MERGED") == "true"

    merge_p = run_script(SCRIPTS / "merge-push.sh", wt)
    assert merge_p.returncode == 0, out(merge_p)
    assert kv(merge_p.stdout, "ALREADY_MERGED") == "true"
    assert kv(merge_p.stdout, "MERGE_COMMIT") == ""  # 不创建空合并提交
    assert kv(merge_p.stdout, "PUSHED") == "true"

    # MERGE_COMMIT 为空：按 SKILL.md 跳过 Close，fake-gh 无任何调用
    assert calls(log) == []

    cleanup_p = run_script(SCRIPTS / "cleanup.sh", wt)
    assert cleanup_p.returncode == 0, out(cleanup_p)
    assert kv(cleanup_p.stdout, "WORKTREE_REMOVED") == "true"
    assert kv(cleanup_p.stdout, "LOCAL_BRANCH_DELETED") == "true"
    assert kv(cleanup_p.stdout, "REMOTE_BRANCH_DELETED") == "true"
    assert section(cleanup_p.stdout, "REMAINING") == ""
    assert str(wt) not in worktree_list(repo)
    assert not has_local_branch(repo, "dev/feature")
    assert "refs/heads/dev/feature" not in remote_refs(repo)


def test_full_flow_already_merged_syncs_when_main_behind(repo_factory):
    """已合入但本地主干落后：跳过 dev 合并与 Close，仍同步推送主干并清理。

    对应 SKILL.md 步骤 3 的 MERGE_COMMIT 语义：已合入时 MERGE_COMMIT 为空（未创建
    dev 合并提交），但主干落后时同步推送仍会产生新同步合并提交（SYNCED=true），
    报告需如实说明而非声称"未产生新提交"。
    """
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, f"feat: 完成功能 (#{ISSUE})")
    push_dev_branch(wt, "dev/feature")
    repo.git("merge", "--no-ff", "dev/feature", "-m", "merge: dev/feature")
    repo.git("push", "-q", "origin", "main")
    # 远程 main 出现新提交（本地主干落后）
    ahead = repo.root / "ahead"
    git("clone", str(repo.remote), str(ahead))
    git("config", "user.name", "Test User", cwd=ahead)
    git("config", "user.email", "test@example.com", cwd=ahead)
    (ahead / "remote.txt").write_text("remote change\n")
    git("add", "-A", cwd=ahead)
    git("commit", "-qm", "chore: remote change", cwd=ahead)
    git("push", "-q", "origin", "main", cwd=ahead)
    gh, log = install_fake_gh(repo, state="OPEN")

    p = run_script(SCRIPTS / "preflight.sh", wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "ALREADY_MERGED") == "true"

    merge_p = run_script(SCRIPTS / "merge-push.sh", wt)
    assert merge_p.returncode == 0, out(merge_p)
    assert kv(merge_p.stdout, "ALREADY_MERGED") == "true"
    assert kv(merge_p.stdout, "SYNCED") == "true"  # 同步了远程主干（产生同步合并提交）
    assert kv(merge_p.stdout, "MERGE_COMMIT") == ""  # 未创建 dev 合并提交
    assert kv(merge_p.stdout, "PUSHED") == "true"

    # MERGE_COMMIT 为空：按 SKILL.md 跳过 Close，fake-gh 无任何调用
    assert calls(log) == []

    # 同步推送生效：远程 main 已含远程新提交
    history = git("log", "--oneline", remote_main_hash(repo), cwd=repo.work).stdout
    assert "remote change" in history

    cleanup_p = run_script(SCRIPTS / "cleanup.sh", wt)
    assert cleanup_p.returncode == 0, out(cleanup_p)
    assert kv(cleanup_p.stdout, "WORKTREE_REMOVED") == "true"
    assert kv(cleanup_p.stdout, "LOCAL_BRANCH_DELETED") == "true"
    assert kv(cleanup_p.stdout, "REMOTE_BRANCH_DELETED") == "true"
    assert section(cleanup_p.stdout, "REMAINING") == ""
    assert str(wt) not in worktree_list(repo)
