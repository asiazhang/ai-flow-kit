"""verify-release.sh：发布后校验（版本文件、CHANGELOG、tag 冲突、发布前命令）。"""

from conftest import kv, out

SCRIPT = "run-release/scripts/verify-release.sh"

ARGS = [
    "--version", "1.2.3",
    "--version-files", "pkg.json:json",
    "--changelog", "CHANGELOG.md",
    "--changelog-style", "top-insert",
    "--tag-prefix", "v",
]


def _write_ok_files(repo):
    (repo.work / "pkg.json").write_text('{"version":"1.2.3"}\n')
    (repo.work / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [1.2.3] - 2026-08-23\n\n- x\n"
    )


def test_all_pass(repo_factory):
    repo = repo_factory()
    _write_ok_files(repo)
    p = repo.script(SCRIPT, *ARGS)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "VERIFY_RESULT") == "PASS"


def test_version_file_mismatch_fails(repo_factory):
    repo = repo_factory()
    _write_ok_files(repo)
    (repo.work / "pkg.json").write_text('{"version":"9.9.9"}\n')
    p = repo.script(SCRIPT, *ARGS)
    assert p.returncode == 1
    assert "FAIL" in p.stdout


def test_existing_tag_fails(repo_factory):
    repo = repo_factory()
    _write_ok_files(repo)
    repo.git("tag", "v1.2.3")
    p = repo.script(SCRIPT, *ARGS)
    assert p.returncode == 1
    assert "FAIL" in p.stdout


def test_missing_changelog_entry_fails(repo_factory):
    repo = repo_factory()
    _write_ok_files(repo)
    (repo.work / "CHANGELOG.md").write_text("# Changelog\n\n## [0.0.1] - 2026-01-01\n")
    p = repo.script(SCRIPT, *ARGS)
    assert p.returncode == 1
    assert "FAIL" in p.stdout


def test_pre_command_failure_fails(repo_factory):
    repo = repo_factory()
    _write_ok_files(repo)
    p = repo.script(SCRIPT, *ARGS, "--command", "false")
    assert p.returncode == 1
    assert "FAIL" in p.stdout


def test_pre_command_pass(repo_factory):
    repo = repo_factory()
    _write_ok_files(repo)
    p = repo.script(SCRIPT, *ARGS, "--command", "true")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "VERIFY_RESULT") == "PASS"


def test_missing_version(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT)
    assert p.returncode == 2


def test_invalid_version(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT, "--version", "abc")
    assert p.returncode == 2
