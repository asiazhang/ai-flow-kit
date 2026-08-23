"""delete-confirmed.sh：候选一致时安全删除，变化时停止。"""

from conftest import out

SCRIPT = "clean-branches/scripts/delete-confirmed.sh"


def _merged_gone_branch(repo, name):
    repo.git("checkout", "-q", "-b", name)
    (repo.work / "feature.txt").write_text("m\n")
    repo.git("add", "feature.txt")
    repo.git("commit", "-qm", f"feat: {name} work")
    repo.git("push", "-q", "-u", "origin", name)
    repo.git("checkout", "-q", "main")
    repo.git("merge", "-q", "--no-ff", name, "-m", f"merge {name}")
    repo.git("push", "-q", "origin", "main")
    repo.git("push", "-q", "origin", f":{name}")


def _unmerged_gone_branch(repo, name):
    repo.git("checkout", "-q", "-b", name)
    (repo.work / "feature.txt").write_text("u\n")
    repo.git("add", "feature.txt")
    repo.git("commit", "-qm", f"feat: {name} work")
    repo.git("push", "-q", "-u", "origin", name)
    repo.git("checkout", "-q", "main")
    repo.git("push", "-q", "origin", f":{name}")


def _local_branches(repo):
    return repo.git("for-each-ref", "--format=%(refname:short)", "refs/heads/").stdout


def test_merged_branch_deleted(repo_factory):
    repo = repo_factory()
    _merged_gone_branch(repo, "dev/merged")
    p = repo.script(SCRIPT, "--expected-branch", "dev/merged")
    assert p.returncode == 0, out(p)
    assert "RESULT=deleted" in p.stdout
    assert "dev/merged" not in _local_branches(repo)


def test_unmerged_branch_retained(repo_factory):
    repo = repo_factory()
    _unmerged_gone_branch(repo, "dev/unmerged")
    p = repo.script(SCRIPT, "--expected-branch", "dev/unmerged")
    assert p.returncode == 0, out(p)
    assert "RESULT=retained" in p.stdout
    assert "dev/unmerged" in _local_branches(repo)


def test_candidate_change_stops_without_deleting(repo_factory):
    repo = repo_factory()
    _unmerged_gone_branch(repo, "dev/gone1")
    p = repo.script(SCRIPT, "--expected-branch", "dev/wrong")
    assert p.returncode == 3
    assert "dev/gone1" in _local_branches(repo)


def test_missing_expected_branch(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT)
    assert p.returncode == 2
