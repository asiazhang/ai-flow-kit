#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  resolve-base.sh

按 new-branch Skill 规定的优先级选择 main 或 master，并输出基础分支
来自本地分支还是 origin。不会切换分支或修改本地引用。
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "不支持的位置参数。使用 --help 查看用法。" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)" || {
  echo "当前目录不在 Git 仓库内，已停止。" >&2
  exit 1
}
cd "$repo_root"

git remote get-url origin >/dev/null 2>&1 || {
  echo "找不到 origin，无法确定基础分支。" >&2
  exit 1
}

current_branch="$(git branch --show-current)"
base_is_local=false

if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
  base_branch="$current_branch"
  base_is_local=true
elif git show-ref --verify --quiet refs/heads/main; then
  base_branch="main"
  base_is_local=true
elif git show-ref --verify --quiet refs/heads/master; then
  base_branch="master"
  base_is_local=true
elif git show-ref --verify --quiet refs/remotes/origin/main; then
  base_branch="main"
elif git show-ref --verify --quiet refs/remotes/origin/master; then
  base_branch="master"
elif git ls-remote --exit-code --heads origin main >/dev/null 2>&1; then
  base_branch="main"
else
  if git ls-remote --exit-code --heads origin master >/dev/null 2>&1; then
    base_branch="master"
  else
    echo "找不到可用的 main/master 基础分支，已停止。" >&2
    exit 1
  fi
fi

printf 'REPO_ROOT=%s\n' "$repo_root"
printf 'CURRENT_BRANCH=%s\n' "$current_branch"
printf 'BASE_BRANCH=%s\n' "$base_branch"
printf 'BASE_IS_LOCAL=%s\n' "$base_is_local"
