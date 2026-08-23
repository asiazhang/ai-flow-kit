"""commit-and-push/verify.sh：推送后验证。"""

from conftest import kv, out, section

SCRIPT = "commit-and-push/scripts/verify.sh"


def test_no_pending_commits(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "UPSTREAM_REF") == "origin/main"
    assert section(p.stdout, "PENDING_COMMITS") == ""


def test_pending_commits_fail(repo_factory):
    repo = repo_factory()
    (repo.work / "x.txt").write_text("x\n")
    repo.git("add", "x.txt")
    repo.git("commit", "-qm", "feat: x")
    p = repo.script(SCRIPT)
    assert p.returncode == 1


def test_no_upstream_fail(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/noup")
    p = repo.script(SCRIPT)
    assert p.returncode == 1
