"""finish-worktree/close-issue.sh：经 GH_BIN 调用 gh 关闭 issue（先留评论，已关闭则跳过）。"""

import os
import subprocess

from conftest import SKILLS, kv, out

SCRIPT = "finish-worktree/scripts/close-issue.sh"

GITHUB_ORIGIN = "git@github.com:asiazhang/ai-flow-kit.git"


def install_fake_gh(repo, *, state="OPEN", view_fails=False) -> tuple:
    """安装 fake-gh 桩：记录每次调用参数（>>> 行），模拟 issue view/comment/close。

    view 返回 {"state": ...}；view_fails 时 view 命令以非零退出（模拟查询失败）。
    """
    fake_dir = repo.root / "fake-gh"
    fake_dir.mkdir(exist_ok=True)
    log = fake_dir / "calls.log"
    gh = fake_dir / "gh"
    if view_fails:
        view_cmd = "exit 1"
    else:
        view_cmd = f"printf '%s\\n' '{state}'"
    gh.write_text(
        f"""#!/bin/sh
printf '>>> %s\\n' "$*" >> {log}
case "$1" in
  issue)
    case "$2" in
      view) {view_cmd} ;;
    esac
    ;;
esac
exit 0
"""
    )
    gh.chmod(0o755)
    return gh, log


def run_close_issue(cwd, issue, *, gh_bin=None, merge_commit=None, env=None):
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    if gh_bin is not None:
        full_env["GH_BIN"] = str(gh_bin)
    if merge_commit is not None:
        full_env["MERGE_COMMIT"] = merge_commit
    return subprocess.run(
        ["bash", str(SKILLS / SCRIPT), str(issue)],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=full_env,
    )


def calls(log) -> list[str]:
    """fake-gh 收到的调用参数行（>>> 前缀）。"""
    return [line[4:] for line in log.read_text().splitlines() if line.startswith(">>> ")]


def test_close_issue_comment_then_close(repo_factory):
    repo = repo_factory()
    repo.git("remote", "set-url", "origin", GITHUB_ORIGIN)
    gh, log = install_fake_gh(repo, state="OPEN")
    merge_commit = "a" * 40

    p = run_close_issue(repo.work, 3, gh_bin=gh, merge_commit=merge_commit)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "ISSUE_NUMBER") == "3"
    assert kv(p.stdout, "REPO") == "asiazhang/ai-flow-kit"
    assert kv(p.stdout, "ISSUE_STATE") == "OPEN"
    assert kv(p.stdout, "COMMENTED") == "true"
    assert kv(p.stdout, "CLOSED") == "true"

    # 调用顺序：view → comment → close；repo 从 origin 解析
    assert calls(log) == [
        "issue view 3 -R asiazhang/ai-flow-kit --json state --jq .state",
        f"issue comment 3 -R asiazhang/ai-flow-kit --body 已通过 finish-worktree 收尾流程合并推送，合并提交：{merge_commit}",
        "issue close 3 -R asiazhang/ai-flow-kit",
    ]


def test_close_issue_repo_from_https_origin(repo_factory):
    repo = repo_factory()
    repo.git("remote", "set-url", "origin", "https://github.com/owner/repo.git")
    gh, log = install_fake_gh(repo, state="OPEN")

    p = run_close_issue(repo.work, 7, gh_bin=gh)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "REPO") == "owner/repo"
    assert calls(log)[0] == "issue view 7 -R owner/repo --json state --jq .state"


def test_close_issue_already_closed_skips(repo_factory):
    repo = repo_factory()
    repo.git("remote", "set-url", "origin", GITHUB_ORIGIN)
    gh, log = install_fake_gh(repo, state="CLOSED")

    p = run_close_issue(repo.work, 3, gh_bin=gh, merge_commit="b" * 40)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "SKIPPED") == "true"
    assert kv(p.stdout, "ISSUE_STATE") == "CLOSED"
    # 幂等：只查询，不评论不关闭
    assert calls(log) == ["issue view 3 -R asiazhang/ai-flow-kit --json state --jq .state"]


def test_close_issue_without_merge_commit(repo_factory):
    repo = repo_factory()
    repo.git("remote", "set-url", "origin", GITHUB_ORIGIN)
    gh, log = install_fake_gh(repo, state="OPEN")

    p = run_close_issue(repo.work, 5, gh_bin=gh)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CLOSED") == "true"
    # 无 MERGE_COMMIT 时评论不注明哈希
    assert "合并提交" not in calls(log)[1]
    assert "已通过 finish-worktree 收尾流程合并推送。" in calls(log)[1]


def test_close_issue_view_failure_stops(repo_factory):
    repo = repo_factory()
    repo.git("remote", "set-url", "origin", GITHUB_ORIGIN)
    gh, log = install_fake_gh(repo, state="OPEN", view_fails=True)

    p = run_close_issue(repo.work, 3, gh_bin=gh)
    assert p.returncode == 1, out(p)
    assert "防误关" in p.stderr
    # 查询失败：不评论、不关闭
    assert len(calls(log)) == 1
    assert calls(log)[0].startswith("issue view")


def test_close_issue_unresolvable_origin_stops(repo_factory):
    repo = repo_factory()  # 默认 origin 为本地路径，无法解析 owner/repo
    gh, _ = install_fake_gh(repo, state="OPEN")

    p = run_close_issue(repo.work, 3, gh_bin=gh)
    assert p.returncode == 1, out(p)
    assert "origin" in p.stderr


def test_close_issue_bad_args(repo_factory):
    repo = repo_factory()
    p = run_close_issue(repo.work, "abc")
    assert p.returncode == 2, out(p)

    p = run_close_issue(repo.work, 0)
    assert p.returncode == 2, out(p)

    p = subprocess.run(
        ["bash", str(SKILLS / SCRIPT)],
        cwd=repo.work,
        capture_output=True,
        text=True,
    )
    assert p.returncode == 2, out(p)


def test_close_issue_help(repo_factory):
    repo = repo_factory()
    p = subprocess.run(
        ["bash", str(SKILLS / SCRIPT), "--help"],
        cwd=repo.work,
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, out(p)
    assert "close-issue.sh" in p.stdout
