"""next-version.sh：语义化版本递增计算（纯计算，无需仓库）。"""

from conftest import REPO_ROOT, out, run_script

SCRIPT = REPO_ROOT / "skills/run-release/scripts/next-version.sh"


def run(*args):
    return run_script(SCRIPT, REPO_ROOT, *args)


def test_patch():
    p = run("--current", "1.2.2", "--bump", "patch")
    assert p.returncode == 0, out(p)
    assert p.stdout.strip() == "1.2.3"


def test_minor():
    p = run("--current", "1.2.2", "--bump", "minor")
    assert p.returncode == 0, out(p)
    assert p.stdout.strip() == "1.3.0"


def test_major():
    p = run("--current", "1.2.2", "--bump", "major")
    assert p.returncode == 0, out(p)
    assert p.stdout.strip() == "2.0.0"


def test_first_release_patch():
    p = run("--current", "0.0.0", "--bump", "patch")
    assert p.returncode == 0, out(p)
    assert p.stdout.strip() == "0.0.1"


def test_cross_digit_clear():
    p = run("--current", "2.9.9", "--bump", "minor")
    assert p.returncode == 0, out(p)
    assert p.stdout.strip() == "2.10.0"


def test_missing_current():
    p = run("--bump", "patch")
    assert p.returncode == 2


def test_missing_bump():
    p = run("--current", "1.0.0")
    assert p.returncode == 2


def test_invalid_version():
    p = run("--current", "abc", "--bump", "patch")
    assert p.returncode == 2


def test_invalid_bump():
    p = run("--current", "1.0.0", "--bump", "big")
    assert p.returncode == 2


def test_unknown_argument():
    p = run("--current", "1.0.0", "--bump", "patch", "--extra")
    assert p.returncode == 2
