"""check-skills-consistency.sh：README 与 plugin.json 的 Skill 列表一致性。"""

from conftest import REPO_ROOT, git, out, run_script

SCRIPT = REPO_ROOT / "scripts/check-skills-consistency.sh"


def test_real_repo_consistent():
    p = run_script(SCRIPT, REPO_ROOT)
    assert p.returncode == 0, out(p)
    assert "OK" in p.stdout


def _make_fake_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".claude-plugin").mkdir(parents=True)
    (repo / "skills" / "a").mkdir(parents=True)
    (repo / "skills" / "b").mkdir(parents=True)
    git("init", "-q", "-b", "main", str(repo))
    (repo / ".claude-plugin" / "plugin.json").write_text(
        '{"skills":["./skills/a","./skills/b"]}\n'
    )
    return repo


def test_inconsistent_readme_fails(tmp_path):
    repo = _make_fake_repo(tmp_path)
    (repo / "README.md").write_text(
        "| Skill | 描述 |\n|-------|------|\n| `a` | x |\n"
    )
    p = run_script(SCRIPT, repo)
    assert p.returncode == 1
    assert "FAIL" in p.stdout


def test_consistent_readme_passes(tmp_path):
    repo = _make_fake_repo(tmp_path)
    (repo / "README.md").write_text(
        "| Skill | 描述 |\n|-------|------|\n| `a` | x |\n| `b` | y |\n"
    )
    p = run_script(SCRIPT, repo)
    assert p.returncode == 0, out(p)
    assert "OK" in p.stdout
