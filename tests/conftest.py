"""pytest 公共设施：临时 Git 仓库、脚本运行、输出解析。

所有测试通过 subprocess 调用仓库内的 bash 脚本（`bash <script>`，
与 SKILL.md 中的调用约定一致），脚本输出经解析函数断言。
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "skills"


# ---------- 通用工具 ----------

def git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """执行 git 命令，失败时抛异常。"""
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} 失败（cwd={cwd}）：{proc.stderr.strip()}"
        )
    return proc


def run_script(script: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """以 bash 运行指定脚本（不 check，退出码交由断言判断）。"""
    return subprocess.run(
        ["bash", str(script), *map(str, args)],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def kv(output: str, key: str) -> str:
    """提取 KEY=VALUE 输出行中的 VALUE。"""
    for line in output.splitlines():
        if line.startswith(f"{key}="):
            return line[len(key) + 1 :]
    return ""


def section(output: str, name: str) -> str:
    """提取区段内容，支持 NAME_BEGIN/NAME_END 与 ---NAME--- 两种标记。"""
    lines = output.splitlines()
    begin, end = f"{name}_BEGIN", f"{name}_END"
    if begin in lines and end in lines:
        i = lines.index(begin) + 1
        j = lines.index(end)
        return "\n".join(lines[i:j])
    marker = f"---{name}---"
    if marker in lines:
        i = lines.index(marker) + 1
        out = []
        for line in lines[i:]:
            if line.startswith("---") and line.endswith("---"):
                break
            out.append(line)
        return "\n".join(out)
    return ""


def out(proc: subprocess.CompletedProcess) -> str:
    """合并 stdout/stderr，便于断言错误时打印上下文。"""
    return f"exit={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"


# ---------- 临时 Git 仓库 ----------


class Repo:
    """带裸远程的临时工作仓库：remote.git + work/，默认分支 main。"""

    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="ai-flow-kit-test-"))
        self.remote = self.root / "remote.git"
        self.work = self.root / "work"
        self._counter = 0

        git("init", "--bare", "--initial-branch=main", str(self.remote))
        git("clone", str(self.remote), str(self.work))
        git("config", "user.name", "Test User", cwd=self.work)
        git("config", "user.email", "test@example.com", cwd=self.work)
        (self.work / "base.txt").write_text("base\n")
        git("add", "base.txt", cwd=self.work)
        git("commit", "-qm", "chore: init", cwd=self.work)
        git("push", "-q", "-u", "origin", "main", cwd=self.work)
        git("remote", "set-head", "origin", "main", cwd=self.work)

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def git(self, *args: str) -> subprocess.CompletedProcess:
        return git(*args, cwd=self.work)

    def commit(self, msg: str, body: str | None = None) -> None:
        """提交一个带内容的文件，可附提交正文（如 BREAKING CHANGE）。"""
        self._counter += 1
        (self.work / f"f{self._counter}.txt").write_text(f"change {self._counter}\n")
        self.git("add", "-A")
        if body:
            self.git("commit", "-qm", msg, "-m", body)
        else:
            self.git("commit", "-qm", msg)

    def script(self, relative: str, *args: str) -> subprocess.CompletedProcess:
        """运行 skills/<skill>/scripts/<name>.sh（相对 skills 目录）。"""
        return run_script(SKILLS / relative, self.work, *args)


@pytest.fixture
def repo_factory():
    """工厂 fixture：每次调用创建一个全新临时仓库，测试结束统一清理。"""
    repos: list[Repo] = []

    def _factory() -> Repo:
        repo = Repo()
        repos.append(repo)
        return repo

    yield _factory
    for repo in repos:
        repo.cleanup()
