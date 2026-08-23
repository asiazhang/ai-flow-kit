"""finish-worktree/preflight.sh：识别 worktree 与合并前状态。"""

from conftest import SKILLS, commit_in, git, kv, out, run_script, section

SCRIPT = "finish-worktree/scripts/preflight.sh"


def run_preflight(cwd):
    return run_script(SKILLS / SCRIPT, cwd)


def test_identifies_worktree_and_branch(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")

    p = run_preflight(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CURRENT_BRANCH") == "dev/feature"
    assert kv(p.stdout, "WORKTREE_PATH") == str(wt)
    assert kv(p.stdout, "MAIN_WORKTREE_PATH") == str(repo.work)
    assert kv(p.stdout, "IS_MAIN_WORKTREE") == "false"
    assert kv(p.stdout, "MAIN_BRANCH") == "main"
    assert kv(p.stdout, "WORKING_TREE_CLEAN") == "true"
    assert kv(p.stdout, "ALREADY_MERGED") == "false"


def test_in_main_worktree(repo_factory):
    repo = repo_factory()
    p = run_preflight(repo.work)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CURRENT_BRANCH") == "main"
    assert kv(p.stdout, "IS_MAIN_WORKTREE") == "true"
    assert kv(p.stdout, "MAIN_WORKTREE_PATH") == str(repo.work)


def test_main_worktree_follows_main_branch(repo_factory):
    """main 分支不在主 worktree 时，MAIN_WORKTREE_PATH 指向 main 所在 worktree。"""
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/other")
    main_path = repo.root / "worktrees" / "main"
    repo.git("worktree", "add", str(main_path), "main")
    wt = repo.add_worktree("feature", "dev/feature")

    p = run_preflight(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "MAIN_WORKTREE_PATH") == str(main_path)
    assert kv(p.stdout, "IS_MAIN_WORKTREE") == "false"

    p_main = run_preflight(main_path)
    assert p_main.returncode == 0, out(p_main)
    assert kv(p_main.stdout, "IS_MAIN_WORKTREE") == "true"


def test_dirty_worktree_stops(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    (wt / "wip.txt").write_text("wip\n")

    p = run_preflight(wt)
    assert p.returncode == 1, out(p)
    assert "commit-and-push" in p.stderr
    assert kv(p.stdout, "WORKING_TREE_CLEAN") == "false"
    assert "wip.txt" in section(p.stdout, "STATUS")


def test_already_merged_flagged(repo_factory):
    repo = repo_factory()
    wt = repo.add_worktree("feature", "dev/feature")
    commit_in(wt, "feat: feature")
    repo.git("merge", "--no-ff", "dev/feature", "-m", "merge: dev/feature")

    p = run_preflight(wt)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "ALREADY_MERGED") == "true"
