"""finish-worktree/cleanup.sh：移除 worktree、删除本地与远程 dev 分支（单项失败不阻断）。"""

import subprocess

from conftest import SKILLS, commit_in, git, kv, out, run_script, section

SCRIPT = "finish-worktree/scripts/cleanup.sh"


def run_cleanup(cwd):
    return run_script(SKILLS / SCRIPT, cwd)


def push_dev_branch(wt, branch: str) -> None:
    """把 dev 分支推送到远程（模拟合并推送成功后远程分支存在）。"""
    git("push", "-q", "-u", "origin", branch, cwd=wt)


def merge_dev_into_main(repo, branch: str) -> None:
    """在主 worktree 内以 --no-ff 合并 dev 分支进 main（模拟 merge-push 成功）。"""
    repo.git("merge", "--no-ff", branch, "-m", f"merge: {branch}")


def worktree_list(repo) -> str:
    return git("worktree", "list", cwd=repo.work).stdout


def has_local_branch(repo, branch: str) -> bool:
    """分支是否存在（conftest.git 对非零退出码抛异常，这里直接 subprocess 判断）。"""
    proc = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/heads/{branch}"],
        cwd=repo.work,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def remote_refs(repo) -> str:
    return git("ls-remote", str(repo.remote)).stdout


def test_cleanup_removes_worktree_and_branches(repo_factory):
    """正常场景：worktree、本地分支、远程分支均被移除/删除。"""
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    push_dev_branch(wt, "dev/feature")
    merge_dev_into_main(repo, "dev/feature")

    p = run_cleanup(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CURRENT_BRANCH") == "dev/feature"
    assert kv(p.stdout, "WORKTREE_REMOVED") == "true"
    assert kv(p.stdout, "LOCAL_BRANCH_DELETED") == "true"
    assert kv(p.stdout, "REMOTE_BRANCH_DELETED") == "true"
    assert section(p.stdout, "REMAINING") == ""

    # worktree 已移除、本地分支已删除、远程分支已删除
    assert str(wt) not in worktree_list(repo)
    assert not has_local_branch(repo, "dev/feature")
    assert "refs/heads/dev/feature" not in remote_refs(repo)


def test_cleanup_untracked_files_retained_without_force(repo_factory):
    """worktree 含未跟踪文件：停止并报告，不 --force；本地分支保留；远程分支仍删除。"""
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    push_dev_branch(wt, "dev/feature")
    merge_dev_into_main(repo, "dev/feature")
    (wt / "keep.txt").write_text("keep me\n")

    p = run_cleanup(wt)
    assert p.returncode == 0, out(p)  # 单项失败不阻断整体
    assert kv(p.stdout, "WORKTREE_REMOVED") == "false"
    assert kv(p.stdout, "LOCAL_BRANCH_DELETED") == "false"  # 分支仍被 worktree 检出
    assert kv(p.stdout, "REMOTE_BRANCH_DELETED") == "true"

    remaining = section(p.stdout, "REMAINING")
    assert "worktree" in remaining
    assert "untracked" in remaining  # 报告原因：含未跟踪文件
    assert "--force" in remaining  # 明确未使用 --force
    assert "本地分支" in remaining

    # 未强制删除：目录与文件仍在，本地分支保留，远程分支已删除
    assert wt.is_dir()
    assert (wt / "keep.txt").read_text() == "keep me\n"
    assert has_local_branch(repo, "dev/feature")
    assert "refs/heads/dev/feature" not in remote_refs(repo)


def test_cleanup_unmerged_branch_retained(repo_factory):
    """本地分支未合并且未推送（无 upstream）：保留并报告，不自动 -D；worktree 照常清理。

    注：git branch -d 的合并判定含 upstream——分支已推送（upstream 存在）时 git
    视为安全删除（提交有远程备份），不会触发保留；此处构造无 upstream 的未合并分支。
    """
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    # 不合并进 main，也不推送（无 upstream，git branch -d 判定 not fully merged）

    p = run_cleanup(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "WORKTREE_REMOVED") == "true"  # 工作区干净可移除
    assert kv(p.stdout, "LOCAL_BRANCH_DELETED") == "false"
    assert kv(p.stdout, "REMOTE_BRANCH_DELETED") == "skipped-gone"

    remaining = section(p.stdout, "REMAINING")
    assert "not fully merged" in remaining  # 报告原因：未合并
    assert "-D" in remaining  # 明确未使用 -D
    assert has_local_branch(repo, "dev/feature")
    assert str(wt) not in worktree_list(repo)


def test_cleanup_remote_branch_already_gone(repo_factory):
    """远程分支已不存在：视为完成（skipped-gone），不报残留。"""
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    merge_dev_into_main(repo, "dev/feature")
    # 从未推送 dev 分支到远程

    p = run_cleanup(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "WORKTREE_REMOVED") == "true"
    assert kv(p.stdout, "LOCAL_BRANCH_DELETED") == "true"
    assert kv(p.stdout, "REMOTE_BRANCH_DELETED") == "skipped-gone"
    assert section(p.stdout, "REMAINING") == ""


def test_cleanup_local_ahead_of_remote_still_deletes(repo_factory):
    """本地 dev 分支领先远程（真实流程：merge-push 只推 main 不更新远程 dev 分支）。

    已合入 main 时，先删远程分支并 remote prune 清理过期跟踪引用，再 branch -d
    可正确判定（相对 HEAD 已合并）；修复前 git 按滞后的 upstream 误报 not fully merged。
    """
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature 1")
    push_dev_branch(wt, "dev/feature")  # 推送过 dev 分支（建立 upstream）
    commit_in(wt, "feat: feature 2")  # 本地领先远程
    merge_dev_into_main(repo, "dev/feature")
    # 远程 dev 分支仍指向旧提交（滞后于本地）

    p = run_cleanup(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "WORKTREE_REMOVED") == "true"
    assert kv(p.stdout, "LOCAL_BRANCH_DELETED") == "true"  # 修复点：不再误判残留
    assert kv(p.stdout, "REMOTE_BRANCH_DELETED") == "true"
    assert section(p.stdout, "REMAINING") == ""

    # 本地/远程分支均已删除，提交保留在 main
    assert not has_local_branch(repo, "dev/feature")
    assert "refs/heads/dev/feature" not in remote_refs(repo)
    history = git("log", "--oneline", "main", cwd=repo.work).stdout
    assert "feat: feature 2" in history


def test_cleanup_partial_failure_does_not_block(repo_factory):
    """单项失败不阻断：worktree 未跟踪 + 未合并，远程分支仍被删除。"""
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    push_dev_branch(wt, "dev/feature")
    # 不合并 + 未跟踪文件并存
    (wt / "keep.txt").write_text("keep me\n")

    p = run_cleanup(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "WORKTREE_REMOVED") == "false"
    assert kv(p.stdout, "LOCAL_BRANCH_DELETED") == "false"
    assert kv(p.stdout, "REMOTE_BRANCH_DELETED") == "true"

    remaining = section(p.stdout, "REMAINING")
    assert "worktree" in remaining
    assert "本地分支" in remaining
    # 远程分支未被阻断，照常清理
    assert "refs/heads/dev/feature" not in remote_refs(repo)


def test_cleanup_idempotent_rerun(repo_factory):
    """部分失败后重跑：已删除项视为完成（不报虚假残留），剩余项继续清理。"""
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    push_dev_branch(wt, "dev/feature")
    merge_dev_into_main(repo, "dev/feature")
    (wt / "keep.txt").write_text("keep me\n")

    # 第一次：worktree 含未跟踪文件导致 remove 失败（本地分支被检出保留），远程分支已删除
    first = run_cleanup(wt)
    assert first.returncode == 0, out(first)
    assert kv(first.stdout, "WORKTREE_REMOVED") == "false"
    assert kv(first.stdout, "REMOTE_BRANCH_DELETED") == "true"
    assert has_local_branch(repo, "dev/feature")

    # 处理掉未跟踪文件后重跑：全部清理完成，远程分支已删除视为完成，无虚假残留
    (wt / "keep.txt").unlink()
    second = run_cleanup(wt)
    assert second.returncode == 0, out(second)
    assert kv(second.stdout, "WORKTREE_REMOVED") == "true"
    assert kv(second.stdout, "LOCAL_BRANCH_DELETED") == "true"
    assert kv(second.stdout, "REMOTE_BRANCH_DELETED") == "skipped-gone"
    assert section(second.stdout, "REMAINING") == ""
    assert str(wt) not in worktree_list(repo)


def test_cleanup_in_main_worktree_stops(repo_factory):
    repo = repo_factory()
    p = run_cleanup(repo.work)
    assert p.returncode == 1, out(p)
    assert "dev worktree" in p.stderr


def test_cleanup_bad_args(repo_factory):
    repo = repo_factory()
    p = run_script(SKILLS / SCRIPT, repo.work, "extra")
    assert p.returncode == 2, out(p)


def test_cleanup_help(repo_factory):
    repo = repo_factory()
    p = run_script(SKILLS / SCRIPT, repo.work, "--help")
    assert p.returncode == 0, out(p)
    assert "cleanup.sh" in p.stdout
