"""discover-gone.sh：发现远程已删除的本地跟踪分支。"""

from conftest import kv, out, section

SCRIPT = "clean-branches/scripts/discover-gone.sh"


def test_no_remote_stops(repo_factory):
    repo = repo_factory()
    repo.git("remote", "remove", "origin")
    p = repo.script(SCRIPT)
    assert p.returncode == 1


def test_no_gone_branches(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "GONE_BRANCH_COUNT") == "0"
    assert "没有需要清理" in p.stdout
    assert section(p.stdout, "GONE_BRANCHES") == ""


def test_gone_branch_detected(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/old")
    (repo.work / "old.txt").write_text("old\n")
    repo.git("add", "old.txt")
    repo.git("commit", "-qm", "feat: old")
    repo.git("push", "-q", "-u", "origin", "dev/old")
    repo.git("checkout", "-q", "main")
    repo.git("push", "-q", "origin", ":dev/old")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "GONE_BRANCH_COUNT") == "1"
    assert "dev/old" in section(p.stdout, "GONE_BRANCHES")


def test_current_branch_gone_stops(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/old")
    (repo.work / "old.txt").write_text("old\n")
    repo.git("add", "old.txt")
    repo.git("commit", "-qm", "feat: old")
    repo.git("push", "-q", "-u", "origin", "dev/old")
    repo.git("checkout", "-q", "main")
    repo.git("push", "-q", "origin", ":dev/old")
    repo.git("checkout", "-q", "dev/old")
    p = repo.script(SCRIPT)
    assert p.returncode == 1
