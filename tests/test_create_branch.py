"""create-branch.sh：同步主干并创建 dev/<description> 分支。"""

from conftest import kv, out

SCRIPT = "new-branch/scripts/create-branch.sh"


def test_clean_create(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT, "--description", "add-widget", "--branch", "dev/add-widget", "--base", "main")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CURRENT_BRANCH") == "dev/add-widget"
    assert kv(p.stdout, "BASE_BRANCH") == "main"
    assert kv(p.stdout, "BASE_SOURCE") == "local"
    assert kv(p.stdout, "STASH_USED") == "false"
    assert kv(p.stdout, "WORKING_TREE_CLEAN") == "true"


def test_dirty_worktree_stash_and_restore(repo_factory):
    repo = repo_factory()
    (repo.work / "base.txt").write_text("base\nchange-1\n")
    p = repo.script(SCRIPT, "--description", "fix-crash", "--branch", "dev/fix-crash", "--base", "main")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "STASH_USED") == "true"
    assert kv(p.stdout, "STASH_RESTORED") == "true"
    assert kv(p.stdout, "CURRENT_BRANCH") == "dev/fix-crash"
    assert kv(p.stdout, "WORKING_TREE_CLEAN") == "false"
    changed = repo.git("diff", "--name-only", "HEAD").stdout
    assert "base.txt" in changed


def test_untracked_file_kept(repo_factory):
    repo = repo_factory()
    (repo.work / "untracked.txt").write_text("untracked\n")
    p = repo.script(SCRIPT, "--description", "add-doc", "--branch", "dev/add-doc", "--base", "main")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "STASH_USED") == "false"
    assert kv(p.stdout, "WORKING_TREE_CLEAN") == "false"
    untracked = repo.git("ls-files", "--others", "--exclude-standard").stdout
    assert "untracked.txt" in untracked


def test_argument_validation(repo_factory):
    repo = repo_factory()
    p = repo.script(SCRIPT, "--description", "AddWidget", "--branch", "dev/AddWidget", "--base", "main")
    assert p.returncode == 2
    p = repo.script(SCRIPT, "--description", "add-widget", "--branch", "dev/other", "--base", "main")
    assert p.returncode == 2
    p = repo.script(SCRIPT, "--description", "add-widget", "--branch", "dev/add-widget", "--base", "develop")
    assert p.returncode == 2
    p = repo.script(SCRIPT, "--description", "add-widget", "--branch", "dev/add-widget")
    assert p.returncode == 2
    long_desc = "a-" * 40
    p = repo.script(SCRIPT, "--description", long_desc, "--branch", f"dev/{long_desc}", "--base", "main")
    assert p.returncode == 2


def test_duplicate_branch_stops(repo_factory):
    repo = repo_factory()
    args = ("--description", "existing", "--branch", "dev/existing", "--base", "main")
    p = repo.script(SCRIPT, *args)
    assert p.returncode == 0, out(p)
    p = repo.script(SCRIPT, *args)
    assert p.returncode == 1


def test_base_from_origin(repo_factory):
    repo = repo_factory()
    repo.git("checkout", "-q", "-b", "dev/x")
    repo.git("branch", "-D", "main")
    p = repo.script(SCRIPT, "--description", "from-origin", "--branch", "dev/from-origin", "--base", "main")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "BASE_SOURCE") == "origin"


def test_local_ahead_still_creates(repo_factory):
    """本地 main 领先 origin/main 时（Already up to date），分支照常创建。"""
    repo = repo_factory()
    repo.commit("feat: ahead of origin")
    p = repo.script(SCRIPT, "--description", "ahead-ok", "--branch", "dev/ahead-ok", "--base", "main")
    assert p.returncode == 0, out(p)
    assert kv(p.stdout, "CURRENT_BRANCH") == "dev/ahead-ok"


def test_diverged_base_stops(repo_factory):
    """本地 main 与 origin/main 分叉时无法 fast-forward → 停止。"""
    from conftest import git

    repo = repo_factory()
    repo.commit("feat: local commit")
    work2 = repo.root / "work2"
    git("clone", str(repo.remote), str(work2))
    git("config", "user.name", "Test User", cwd=work2)
    git("config", "user.email", "test@example.com", cwd=work2)
    (work2 / "remote.txt").write_text("remote\n")
    git("add", "remote.txt", cwd=work2)
    git("commit", "-qm", "feat: remote commit", cwd=work2)
    git("push", "-q", "origin", "main", cwd=work2)
    repo.git("checkout", "-q", "-b", "dev/y")
    p = repo.script(SCRIPT, "--description", "not-ff", "--branch", "dev/not-ff", "--base", "main")
    assert p.returncode == 1
