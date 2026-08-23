"""inspect-staged.sh：暂存区安全检查（阻止路径）。"""

from conftest import kv, out, section

SCRIPT = "commit-and-push/scripts/inspect-staged.sh"


def test_normal_staging(repo_factory):
    repo = repo_factory()
    (repo.work / "a.txt").write_text("hello\n")
    repo.git("add", "a.txt")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "STAGED_FILE_COUNT") == "1"
    assert "a.txt" in section(p.stdout, "STAGED_NAME_STATUS")
    assert "STAGED_DIFF_BEGIN" in p.stdout


def test_env_blocked(repo_factory):
    repo = repo_factory()
    (repo.work / ".env").write_text("SECRET=1\n")
    repo.git("add", ".env")
    p = repo.script(SCRIPT)
    assert p.returncode == 3
    assert ".env" in section(p.stdout, "BLOCKED_PATHS")


def test_pem_blocked(repo_factory):
    repo = repo_factory()
    (repo.work / "server.pem").write_text("KEY\n")
    repo.git("add", "server.pem")
    p = repo.script(SCRIPT)
    assert p.returncode == 3


def test_mixed_normal_and_blocked(repo_factory):
    repo = repo_factory()
    (repo.work / "a.txt").write_text("hello\n")
    (repo.work / "server.pem").write_text("KEY\n")
    repo.git("add", "-A")
    p = repo.script(SCRIPT)
    assert p.returncode == 3
    assert "server.pem" in section(p.stdout, "BLOCKED_PATHS")


def test_empty_staging(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "STAGED_FILE_COUNT") == "0"
