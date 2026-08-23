"""resolve-base.sh：选择 main/master 基础分支。"""

from conftest import kv, out

SCRIPT = "new-branch/scripts/resolve-base.sh"


def test_current_on_main(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "BASE_BRANCH") == "main"
    assert kv(p.stdout, "BASE_IS_LOCAL") == "true"


def test_local_main_preferred(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/foo")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "BASE_BRANCH") == "main"
    assert kv(p.stdout, "BASE_IS_LOCAL") == "true"


def test_origin_main_when_no_local(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/foo")
    repo.git("branch", "-D", "main")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "BASE_BRANCH") == "main"
    assert kv(p.stdout, "BASE_IS_LOCAL") == "false"


def test_local_master_fallback(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "master")
    repo.git("branch", "-D", "main")
    repo.git("checkout", "-q", "-b", "dev/foo2")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "BASE_BRANCH") == "master"
    assert kv(p.stdout, "BASE_IS_LOCAL") == "true"


def test_no_main_master_anywhere_stops(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/foo2")
    repo.git("branch", "-D", "main")
    repo.git("push", "-q", "origin", "dev/foo2:keep")
    repo.git("--git-dir", str(repo.remote), "symbolic-ref", "HEAD", "refs/heads/keep")
    repo.git("push", "-q", "origin", ":main")
    p = repo.script(SCRIPT)
    assert p.returncode == 1


def test_no_origin_stops(repo_factory):
    repo = repo_factory()
    repo.git("remote", "remove", "origin")
    p = repo.script(SCRIPT)
    assert p.returncode == 1
