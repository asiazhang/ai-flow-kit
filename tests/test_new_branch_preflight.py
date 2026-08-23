"""new-branch/preflight.sh：确认仓库可切换。"""

from pathlib import Path

from conftest import kv, out

SCRIPT = "new-branch/scripts/preflight.sh"


def test_clean_repo(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "WORKING_TREE_CLEAN") == "true"
    assert kv(p.stdout, "ORIGIN_AVAILABLE") == "true"
    assert kv(p.stdout, "GIT_OPERATION_IN_PROGRESS") == "false"


def test_dirty_worktree_marked(repo_factory):
    repo = repo_factory()
    (repo.work / "base.txt").write_text("dirty\n")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "WORKING_TREE_CLEAN") == "false"


def test_no_origin_stops(repo_factory):
    repo = repo_factory()
    repo.git("remote", "remove", "origin")
    p = repo.script(SCRIPT)
    assert p.returncode == 1


def test_in_progress_operation_stops(repo_factory):
    repo = repo_factory()
    cherry = repo.git("rev-parse", "--git-path", "CHERRY_PICK_HEAD").stdout.strip()
    (repo.work / cherry).write_text("dummy\n")
    p = repo.script(SCRIPT)
    assert p.returncode == 1
