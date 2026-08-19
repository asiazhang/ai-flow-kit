#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  discover-gone.sh

刷新所有远程的远程跟踪分支，并输出 upstream 状态为 [gone] 的本地分支。
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

remotes="$(git remote)"
if [[ -z "$remotes" ]]; then
  echo "当前仓库没有远程，无法判断远程已删除分支。" >&2
  exit 1
fi

git fetch --prune --all >/dev/null || {
  echo "同步远程失败，已停止，未使用可能过期的分支状态。" >&2
  exit 1
}

current_branch="$(git branch --show-current)"
gone_branches=()
while IFS=$'\t' read -r branch upstream_track; do
  if [[ "$upstream_track" == "[gone]" ]]; then
    gone_branches+=("$branch")
  fi
done < <(git for-each-ref \
  --format='%(refname:short)%09%(upstream:track)' \
  refs/heads/)

for branch in "${gone_branches[@]}"; do
  if [[ "$branch" == "$current_branch" ]]; then
    echo "当前分支 $current_branch 的远程跟踪分支已删除，请先切换到其他分支后重试。" >&2
    exit 1
  fi
done

printf 'REPO_ROOT=%s\n' "$repo_root"
printf 'CURRENT_BRANCH=%s\n' "$current_branch"
printf 'GONE_BRANCH_COUNT=%s\n' "${#gone_branches[@]}"
echo "GONE_BRANCHES_BEGIN"
if [[ "${#gone_branches[@]}" -gt 0 ]]; then
  printf '%s\n' "${gone_branches[@]}"
fi
echo "GONE_BRANCHES_END"
if [[ "${#gone_branches[@]}" -eq 0 ]]; then
  echo "SUMMARY_STATUS=本地仓库没有需要清理的失效分支。"
fi
