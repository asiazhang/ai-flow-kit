"""run-release/preflight.sh：发布前前置检查（分支、工作区、同步、空白）。"""

from conftest import kv, out

SCRIPT = "run-release/scripts/preflight.sh"


def test_pass_on_clean_trunk(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT, "--trunk", "main")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "PREFLIGHT_RESULT") == "PASS"


def test_non_trunk_branch_fails(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/foo")
    p = repo.script(SCRIPT, "--trunk", "main")
    assert p.returncode == 1
    assert "FAIL" in p.stdout


def test_dirty_worktree_fails(repo_factory):
    repo = repo_factory()
    (repo.work / "base.txt").write_text("dirty\n")
    p = repo.script(SCRIPT, "--trunk", "main")
    assert p.returncode == 1
    assert "FAIL" in p.stdout


def test_ahead_of_origin_fails(repo_factory):
    repo = repo_factory()
    repo.commit("feat: local ahead")
    p = repo.script(SCRIPT, "--trunk", "main")
    assert p.returncode == 1
    assert "FAIL" in p.stdout


def test_missing_trunk_value(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT, "--trunk")
    assert p.returncode == 2
