#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  preflight.sh

定位仓库、确认当前处于具名分支，并解析当前分支的 upstream 或默认 origin
推送目标。输出工作区状态和已有待推送提交，不执行提交或推送。
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
if [[ -z "$current_branch" ]]; then
  echo "当前处于 detached HEAD，请先切换到具名分支。" >&2
  exit 1
fi

status="$(git status --porcelain)"
upstream_remote="$(git config --get "branch.$current_branch.remote" || true)"
upstream_merge="$(git config --get "branch.$current_branch.merge" || true)"

if [[ -n "$upstream_remote" && "$upstream_remote" != "." && -n "$upstream_merge" ]]; then
  push_remote="$upstream_remote"
  push_branch="${upstream_merge#refs/heads/}"
  upstream_ref="$push_remote/$push_branch"
  push_refspec="HEAD:$push_branch"
  has_upstream=true
  git remote get-url "$push_remote" >/dev/null 2>&1 || {
    echo "upstream 远程 $push_remote 不存在，已停止。" >&2
    exit 1
  }
else
  push_remote="origin"
  push_branch="$current_branch"
  upstream_ref=""
  push_refspec="HEAD"
  has_upstream=false
  git remote get-url "$push_remote" >/dev/null 2>&1 || {
    echo "当前分支没有可用 upstream，且找不到 origin，已停止。" >&2
    exit 1
  }
fi

remote_url="$(git remote get-url "$push_remote")"
case "$remote_url" in
  *://*@*)
    remote_url="${remote_url%%://*}://***@${remote_url#*@}"
    ;;
esac

printf 'REPO_ROOT=%s\n' "$repo_root"
printf 'CURRENT_BRANCH=%s\n' "$current_branch"
printf 'PUSH_REMOTE=%s\n' "$push_remote"
printf 'PUSH_BRANCH=%s\n' "$push_branch"
printf 'PUSH_REMOTE_URL=%s\n' "$remote_url"
printf 'PUSH_REFSPEC=%s\n' "$push_refspec"
printf 'HAS_UPSTREAM=%s\n' "$has_upstream"
printf 'UPSTREAM_REF=%s\n' "$upstream_ref"
if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
  echo "IS_PROTECTED_BRANCH=true"
else
  echo "IS_PROTECTED_BRANCH=false"
fi

if [[ -n "$status" ]]; then
  echo "WORKING_TREE_CLEAN=false"
  echo "STATUS_BEGIN"
  printf '%s\n' "$status"
  echo "STATUS_END"
else
  echo "WORKING_TREE_CLEAN=true"
fi

if [[ "$has_upstream" == true ]]; then
  pending_commits="$(git --no-pager log "$upstream_ref..HEAD" --oneline)"
else
  pending_commits=""
fi

echo "PENDING_COMMITS_BEGIN"
printf '%s\n' "$pending_commits"
echo "PENDING_COMMITS_END"
