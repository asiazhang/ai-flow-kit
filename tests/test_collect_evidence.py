"""collect-evidence.sh：收集分支相对主干的变更证据。"""

from conftest import kv, out, section

SCRIPT = "branch-summary/scripts/collect-evidence.sh"


def test_branch_with_commits(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/feature")
    repo.commit("feat: add widget")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CURRENT_BRANCH") == "dev/feature"
    assert kv(p.stdout, "BASE_REF") == "origin/main"
    assert kv(p.stdout, "BRANCH_MERGED") == "false"
    assert kv(p.stdout, "COMMITTED_CHANGES") == "true"
    assert "feat: add widget" in section(p.stdout, "COMMITS")
    assert "DIFF_STAT_BEGIN" in p.stdout
    assert "DIFF_BEGIN" in p.stdout


def test_no_changes(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/empty")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "COMMITTED_CHANGES") == "false"
    assert "没有已提交文件变更" in p.stdout


def test_merged_branch_falls_back(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/merged")
    repo.commit("feat: merged work")
    repo.git("checkout", "-q", "main")
    repo.git("merge", "-q", "--no-ff", "dev/merged", "-m", "merge dev/merged")
    repo.git("push", "-q", "origin", "main")
    repo.git("checkout", "-q", "dev/merged")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "BRANCH_MERGED") == "true"
    assert kv(p.stdout, "MERGE_COMMIT") != ""
    assert "feat: merged work" in section(p.stdout, "COMMITS")


def test_no_origin_uses_local_main(repo_factory):
    repo = repo_factory()
    repo.git("remote", "remove", "origin")
    repo.git("checkout", "-q", "-b", "dev/noorigin")
    repo.commit("feat: no origin")
    p = repo.script(SCRIPT)
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "BASE_REF") == "main"
