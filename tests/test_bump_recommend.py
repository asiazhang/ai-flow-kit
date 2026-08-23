"""bump-recommend.sh：按约定式提交判定版本递增建议。"""

from conftest import kv, out, run_script, section

SCRIPT = "run-release/scripts/bump-recommend.sh"


def test_mixed_feat_fix(repo_factory):
    repo = repo_factory()
    base = repo.git("rev-parse", "HEAD").stdout.strip()
    repo.commit("feat: add widget")
    repo.commit("fix: crash bug")
    p = repo.script(SCRIPT, "--base", base)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "COMMIT_COUNT") == "2"
    assert kv(p.stdout, "NO_CHANGES") == "0"
    assert kv(p.stdout, "SUGGESTED_BUMP") == "minor"
    assert "feat: add widget" in section(p.stdout, "MATCHED_MINOR")
    assert "fix: crash bug" in section(p.stdout, "MATCHED_PATCH")
    assert section(p.stdout, "MATCHED_MAJOR") == ""


def test_breaking_change_body_is_major(repo_factory):
    repo = repo_factory()
    base = repo.git("rev-parse", "HEAD").stdout.strip()
    repo.commit("feat: new api", "BREAKING CHANGE: interface changed")
    p = repo.script(SCRIPT, "--base", base)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "SUGGESTED_BUMP") == "major"
    assert "WARN" in p.stdout
    assert "feat: new api" in section(p.stdout, "MATCHED_MAJOR")


def test_bang_marker_is_major(repo_factory):
    repo = repo_factory()
    base = repo.git("rev-parse", "HEAD").stdout.strip()
    repo.commit("feat!: drop v1 support")
    p = repo.script(SCRIPT, "--base", base)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "SUGGESTED_BUMP") == "major"


def test_untyped_is_patch_with_warn(repo_factory):
    repo = repo_factory()
    base = repo.git("rev-parse", "HEAD").stdout.strip()
    repo.commit("tweak wording")
    p = repo.script(SCRIPT, "--base", base)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "SUGGESTED_BUMP") == "patch"
    assert "WARN" in p.stdout
    assert "tweak wording" in section(p.stdout, "MATCHED_UNTYPED")


def test_no_changes(repo_factory):
    repo = repo_factory()
    base = repo.git("rev-parse", "HEAD").stdout.strip()
    p = repo.script(SCRIPT, "--base", base)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "COMMIT_COUNT") == "0"
    assert kv(p.stdout, "NO_CHANGES") == "1"


def test_since_tag(repo_factory):
    repo = repo_factory()
    repo.git("tag", "v1.0.0")
    repo.commit("fix: since tag fix")
    p = repo.script(SCRIPT, "--since-tag")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "SUGGESTED_BUMP") == "patch"
    assert kv(p.stdout, "COMMIT_COUNT") == "1"


def test_since_tag_without_tag_counts_all(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT, "--since-tag")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "COMMIT_COUNT") == "1"
