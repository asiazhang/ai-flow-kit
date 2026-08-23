"""commit-and-push/preflight.sh：固定提交与推送目标。"""

from conftest import kv, out

SCRIPT = "commit-and-push/scripts/preflight.sh"


def _branch_with_upstream(repo, name="dev/foo"):
    repo.git("checkout", "-q", "-b", name)
    (repo.work / "foo.txt").write_text("x\n")
    repo.git("add", "foo.txt")
    repo.git("commit", "-qm", "feat: foo")
    repo.git("push", "-q", "-u", "origin", name)


def test_with_upstream(repo_factory):
    repo = repo_factory()
    _branch_with_upstream(repo)
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "HAS_UPSTREAM") == "true"
    assert kv(p.stdout, "PUSH_REMOTE") == "origin"
    assert kv(p.stdout, "PUSH_BRANCH") == "dev/foo"
    assert kv(p.stdout, "UPSTREAM_REF") == "origin/dev/foo"
    assert kv(p.stdout, "PENDING_BASE") == "origin/dev/foo"
    assert kv(p.stdout, "IS_PROTECTED_BRANCH") == "false"
    assert kv(p.stdout, "WORKING_TREE_CLEAN") == "true"


def test_main_is_protected(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "IS_PROTECTED_BRANCH") == "true"
    assert kv(p.stdout, "PENDING_BASE") == "origin/main"


def test_without_upstream_falls_back_to_origin_main(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/bar")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "HAS_UPSTREAM") == "false"
    assert kv(p.stdout, "PUSH_REMOTE") == "origin"
    assert kv(p.stdout, "PUSH_REFSPEC") == "HEAD"
    assert kv(p.stdout, "PENDING_BASE") == "origin/main"


def test_dirty_worktree(repo_factory):
    repo = repo_factory()
    (repo.work / "base.txt").write_text("dirty\n")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "WORKING_TREE_CLEAN") == "false"


def test_detached_head_stops(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "--detach", "HEAD")
    p = repo.script(SCRIPT)
    assert p.returncode == 1


def test_no_origin_and_no_upstream_stops(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/no-remote")
    repo.git("remote", "remove", "origin")
    p = repo.script(SCRIPT)
    assert p.returncode == 1
