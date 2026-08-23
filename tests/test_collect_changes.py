"""collect-changes.sh：收集基线以来的变更事实。"""

from conftest import kv, out, run_script

SCRIPT = "run-release/scripts/collect-changes.sh"


def test_explicit_base(repo_factory):
    repo = repo_factory()
    base = repo.git("rev-parse", "HEAD").stdout.strip()
    repo.commit("feat: a")
    repo.commit("fix: b")
    p = repo.script(SCRIPT, "--base", base)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "BASE_REF") == base
    assert kv(p.stdout, "COMMIT_COUNT") == "2"
    assert "feat: a" in p.stdout
    assert "---FILES---" in p.stdout
    assert "---STAT---" in p.stdout


def test_since_tag_without_tag_counts_all(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT, "--since-tag")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "BASE_REF") == ""
    assert kv(p.stdout, "COMMIT_COUNT") == "1"


def test_since_tag(repo_factory):
    repo = repo_factory()
    repo.git("tag", "v2.0.0")
    repo.commit("feat: after tag")
    p = repo.script(SCRIPT, "--since-tag")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "BASE_REF") == "v2.0.0"
    assert kv(p.stdout, "COMMIT_COUNT") == "1"


def test_base_missing_value(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT, "--base")
    assert p.returncode == 2


def test_unknown_argument(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT, "--since-tag", "--extra")
    assert p.returncode == 2


def test_not_in_git_repo(tmp_path):
    from conftest import REPO_ROOT
    p = run_script(REPO_ROOT / "skills/run-release/scripts/collect-changes.sh", tmp_path)
    assert p.returncode == 1
