"""detect-project.sh：探测项目发布约定（tag 版本、CHANGELOG、主干、配置覆盖）。"""

import json

from conftest import kv, out

SCRIPT = "run-release/scripts/detect-project.sh"


def test_default_detection(repo_factory):
    repo = repo_factory()
    repo.git("tag", "v1.2.2")
    (repo.work / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.2.2] - 2026-08-22\n"
    )
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CURRENT_VERSION") == "1.2.2"
    assert kv(p.stdout, "TAG_PREFIX") == "v"
    assert kv(p.stdout, "CHANGELOG") == "CHANGELOG.md"
    assert kv(p.stdout, "CHANGELOG_STYLE") == "unreleased"
    assert kv(p.stdout, "TRUNK_BRANCH") == "main"
    assert kv(p.stdout, "AUTO_PUSH") == "false"


def test_no_tag_is_first_release(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CURRENT_VERSION") == "0.0.0"
    assert kv(p.stdout, "TAG_PREFIX") == "v"


def test_no_changelog_is_none(repo_factory):
    repo = repo_factory()
    repo.git("tag", "v0.1.0")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CHANGELOG") == ""
    assert kv(p.stdout, "CHANGELOG_STYLE") == "none"


def test_changelog_without_unreleased_is_top_insert(repo_factory):
    repo = repo_factory()
    (repo.work / "CHANGELOG.md").write_text("# Changelog\n\n## [0.1.0] - 2026-01-01\n")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CHANGELOG_STYLE") == "top-insert"


def test_run_release_json_overrides(repo_factory):
    repo = repo_factory()
    (repo.work / ".run-release.json").write_text(
        json.dumps(
            {
                "versionFiles": [{"path": "pkg.json", "kind": "json"}],
                "changelog": "HISTORY.md",
                "tagPrefix": "r",
                "trunkBranch": "trunk",
                "autoPush": True,
            }
        )
    )
    (repo.work / "HISTORY.md").write_text("# History\n")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "VERSION_FILES") == "pkg.json:json"
    assert kv(p.stdout, "CHANGELOG") == "HISTORY.md"
    assert kv(p.stdout, "TAG_PREFIX") == "r"
    assert kv(p.stdout, "TRUNK_BRANCH") == "trunk"
    assert kv(p.stdout, "AUTO_PUSH") == "true"


def test_package_json_test_command(repo_factory):
    repo = repo_factory()
    (repo.work / "package.json").write_text('{"scripts":{"test":"echo ok"}}\n')
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "TEST_COMMAND") == "npm test"


def test_no_local_trunk(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/only")
    repo.git("branch", "-D", "main")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "TRUNK_BRANCH") == ""
