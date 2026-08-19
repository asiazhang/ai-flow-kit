#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  collect-evidence.sh

定位当前 Git 仓库，刷新 origin 的远程跟踪分支，选择 main/master 作为比较基准，
并输出当前分支相对基准的提交、统计信息和完整 diff。
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

current_branch="$(git branch --show-current)"
working_tree="$(git status --short)"

if git remote get-url origin >/dev/null 2>&1; then
  git fetch --prune origin >/dev/null || {
    echo "同步 origin 失败，已停止，未使用可能过期的比较基准。" >&2
    exit 1
  }

  if git show-ref --verify --quiet refs/remotes/origin/main; then
    base_ref="origin/main"
  elif git show-ref --verify --quiet refs/remotes/origin/master; then
    base_ref="origin/master"
  else
    echo "origin 中找不到 main 或 master，无法确定主干。" >&2
    exit 1
  fi
else
  if git show-ref --verify --quiet refs/heads/main; then
    base_ref="main"
  elif git show-ref --verify --quiet refs/heads/master; then
    base_ref="master"
  else
    echo "没有 origin，且本地找不到 main 或 master，已停止。" >&2
    exit 1
  fi
fi

git rev-parse --verify "$base_ref^{commit}" >/dev/null || {
  echo "无法解析比较基准 $base_ref，已停止。" >&2
  exit 1
}

printf 'REPO_ROOT=%s\n' "$repo_root"
printf 'CURRENT_BRANCH=%s\n' "$current_branch"
printf 'BASE_REF=%s\n' "$base_ref"

if [[ -n "$working_tree" ]]; then
  echo "WORKING_TREE_CLEAN=false"
  echo "WORKING_TREE_BEGIN"
  printf '%s\n' "$working_tree"
  echo "WORKING_TREE_END"
else
  echo "WORKING_TREE_CLEAN=true"
fi

echo "COMMITS_BEGIN"
git --no-pager log "$base_ref..HEAD" --oneline
echo "COMMITS_END"

if git diff --quiet "$base_ref...HEAD"; then
  echo "COMMITTED_CHANGES=false"
  echo "SUMMARY_STATUS=没有已提交文件变更。"
  exit 0
fi

echo "COMMITTED_CHANGES=true"
echo "DIFF_STAT_BEGIN"
git --no-pager diff --stat "$base_ref...HEAD"
echo "DIFF_STAT_END"
echo "DIFF_BEGIN"
git --no-pager diff --find-renames "$base_ref...HEAD"
echo "DIFF_END"
