"""finish-worktree/extract-issue.sh：从分支提交信息提取 issue 引用候选列表。"""

import subprocess

from conftest import SKILLS, commit_in, git, kv, out, run_script, section

SCRIPT = "finish-worktree/scripts/extract-issue.sh"


def run_extract(cwd):
    return run_script(SKILLS / SCRIPT, cwd)


def test_extract_issue_plain_and_closes(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: #123 实现登录")
    commit_in(wt, "feat: 收尾登录模块", body="Closes #456")

    p = run_extract(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CURRENT_BRANCH") == "dev/feature"
    assert kv(p.stdout, "MAIN_BRANCH") == "main"
    assert kv(p.stdout, "ISSUE_COUNT") == "2"
    assert kv(p.stdout, "CLOSES_COUNT") == "1"
    # 关闭关键词引用优先区段：只有 #456
    assert section(p.stdout, "CLOSES") == "456"
    # 全部引用（git log 从新到旧：最新提交的 #456 在前）
    assert section(p.stdout, "CANDIDATES") == "456\n123"


def test_extract_issue_fixes_in_subject(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "Fixes #789: 修复崩溃")

    p = run_extract(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CLOSES_COUNT") == "1"
    assert section(p.stdout, "CLOSES") == "789"
    assert section(p.stdout, "CANDIDATES") == "789"


def test_extract_issue_no_reference_empty(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: 无关联 issue 的提交")

    p = run_extract(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "ISSUE_COUNT") == "0"
    assert kv(p.stdout, "CLOSES_COUNT") == "0"
    assert section(p.stdout, "CANDIDATES") == ""
    assert section(p.stdout, "CLOSES") == ""


def test_extract_issue_dedupe_across_commits(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: #123 第一步")
    commit_in(wt, "feat: #123 第二步")
    commit_in(wt, "feat: 收尾", body="Closes #123")

    p = run_extract(wt)
    assert p.returncode == 0, out(p)
    # 去重：candidates 与 closes 各只出现一次
    assert kv(p.stdout, "ISSUE_COUNT") == "1"
    assert kv(p.stdout, "CLOSES_COUNT") == "1"
    assert section(p.stdout, "CANDIDATES") == "123"
    assert section(p.stdout, "CLOSES") == "123"


def test_extract_issue_already_merged_empty(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: #123 已合入")
    # 先把 dev 合入 main：分支不再有独有提交
    repo.git("merge", "--no-ff", "dev/feature", "-m", "merge: dev/feature")
    repo.git("push", "-q", "origin", "main")

    p = run_extract(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "ISSUE_COUNT") == "0"
    assert section(p.stdout, "CANDIDATES") == ""


def test_extract_issue_in_main_worktree_empty(repo_factory):
    repo = repo_factory()
    p = run_extract(repo.work)
    assert p.returncode == 0, out(p)
    # main 上无独有提交，无候选
    assert kv(p.stdout, "CURRENT_BRANCH") == "main"
    assert kv(p.stdout, "ISSUE_COUNT") == "0"


def test_extract_issue_help(repo_factory):
    repo = repo_factory()
    p = subprocess.run(
        ["bash", str(SKILLS / SCRIPT), "--help"],
        cwd=repo.work,
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, out(p)
    assert "extract-issue.sh" in p.stdout
