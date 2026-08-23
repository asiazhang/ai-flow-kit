"""resolve-push-target.sh：刷新远程状态并解析推送目标。"""

from conftest import git, kv, out, section

SCRIPT = "commit-and-push/scripts/resolve-push-target.sh"


def _branch_with_upstream(repo, name="dev/foo"):
    repo.git("checkout", "-q", "-b", name)
    (repo.work / "foo.txt").write_text("x\n")
    repo.git("add", "foo.txt")
    repo.git("commit", "-qm", "feat: foo")
    repo.git("push", "-q", "-u", "origin", name)


def test_synced_upstream(repo_factory):
    repo = repo_factory()
    _branch_with_upstream(repo)
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "HAS_UPSTREAM") == "true"
    assert kv(p.stdout, "PENDING_BASE") == "origin/dev/foo"
    assert kv(p.stdout, "REMOTE_AHEAD") == "false"
    assert section(p.stdout, "PENDING_COMMITS") == ""


def test_local_pending_commits(repo_factory):
    repo = repo_factory()
    _branch_with_upstream(repo)
    (repo.work / "y.txt").write_text("y\n")
    repo.git("add", "y.txt")
    repo.git("commit", "-qm", "feat: y")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert "feat: y" in section(p.stdout, "PENDING_COMMITS")
    assert kv(p.stdout, "REMOTE_AHEAD") == "false"


def test_remote_ahead_detected(repo_factory):
    repo = repo_factory()
    _branch_with_upstream(repo)
    # 第二工作副本模拟远端新增提交
    work2 = repo.root / "work2"
    git("clone", str(repo.remote), str(work2))
    git("config", "user.name", "Test User", cwd=work2)
    git("config", "user.email", "test@example.com", cwd=work2)
    git("checkout", "-q", "-b", "dev/foo", "--track", "origin/dev/foo", cwd=work2)
    (work2 / "remote.txt").write_text("remote\n")
    git("add", "remote.txt", cwd=work2)
    git("commit", "-qm", "feat: from remote", cwd=work2)
    git("push", "-q", "origin", "dev/foo", cwd=work2)

    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "REMOTE_AHEAD") == "true"
    assert "feat: from remote" in section(p.stdout, "BEHIND_COMMITS")


def test_without_upstream(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/baz")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "HAS_UPSTREAM") == "false"
    assert kv(p.stdout, "PUSH_REFSPEC") == "HEAD"
    assert kv(p.stdout, "PENDING_BASE") == "origin/main"
