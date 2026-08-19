#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  resolve-push-target.sh

重新解析当前分支的推送目标；有 upstream 时先刷新远程跟踪分支，
然后输出待推送提交和工作区状态。不执行推送。
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
  git fetch "$push_remote" "$push_branch" >/dev/null || {
    echo "更新推送目标 $upstream_ref 失败，已停止。" >&2
    exit 1
  }
  pending_commits="$(git --no-pager log "$upstream_ref..HEAD" --oneline)"
  behind_commits="$(git --no-pager log "HEAD..$upstream_ref" --oneline)"
  if [[ -n "$behind_commits" ]]; then
    remote_ahead=true
  else
    remote_ahead=false
  fi
else
  push_remote="origin"
  push_branch="$current_branch"
  upstream_ref=""
  push_refspec="HEAD"
  has_upstream=false
  git remote get-url "$push_remote" >/dev/null 2>&1 || {
    echo "找不到 $push_remote，已停止。" >&2
    exit 1
  }
  pending_commits="$(git --no-pager log -1 --oneline HEAD)"
  behind_commits=""
  remote_ahead=false
fi

status="$(git status --porcelain)"
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

echo "PENDING_COMMITS_BEGIN"
printf '%s\n' "$pending_commits"
echo "PENDING_COMMITS_END"
printf 'REMOTE_AHEAD=%s\n' "$remote_ahead"
echo "BEHIND_COMMITS_BEGIN"
printf '%s\n' "$behind_commits"
echo "BEHIND_COMMITS_END"

if [[ -n "$status" ]]; then
  echo "WORKING_TREE_CLEAN=false"
  echo "STATUS_BEGIN"
  printf '%s\n' "$status"
  echo "STATUS_END"
else
  echo "WORKING_TREE_CLEAN=true"
fi
