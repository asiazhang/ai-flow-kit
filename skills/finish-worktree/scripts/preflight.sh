#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  preflight.sh

识别当前分支与 worktree、校验工作区已提交干净、检测当前分支是否已合入主干。
输出 KEY=VALUE 与区段标记，不执行合并或推送。

工作区存在未提交修改时以非零状态停止，并提示先运行 commit-and-push。
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

# 主干分支：本仓库约定为 main（仅支持 main，见 Spec Out of Scope）
main_branch="main"
if ! git rev-parse -q --verify "refs/heads/$main_branch" >/dev/null 2>&1 \
  && ! git rev-parse -q --verify "refs/remotes/origin/$main_branch" >/dev/null 2>&1; then
  main_branch=""
fi

# 定位 main 分支所在 worktree（porcelain 中 branch refs/heads/main 所在项）；
# 未检出时回退主 worktree（porcelain 第一项）
main_wt_path=""
wt_path=""
while IFS= read -r line; do
  case "$line" in
    worktree\ *)
      wt_path="${line#worktree }"
      ;;
    branch\ refs/heads/"${main_branch}")
      main_wt_path="${wt_path}"
      break
      ;;
  esac
done < <(git worktree list --porcelain)

if [[ -z "$main_wt_path" ]]; then
  main_wt_path="$(git worktree list --porcelain | sed -n '1s/^worktree //p')"
fi

if [[ -z "$main_wt_path" ]]; then
  main_wt_path="$repo_root"
fi

if [[ "$repo_root" == "$main_wt_path" ]]; then
  is_main_worktree=true
else
  is_main_worktree=false
fi

already_merged=false
if [[ -n "$main_branch" ]]; then
  if git rev-parse -q --verify "refs/heads/$main_branch" >/dev/null 2>&1; then
    main_ref="refs/heads/$main_branch"
  else
    main_ref="refs/remotes/origin/$main_branch"
  fi
  if git merge-base --is-ancestor "$current_branch" "$main_ref" 2>/dev/null; then
    already_merged=true
  fi
fi

status="$(git status --porcelain)"

printf 'REPO_ROOT=%s\n' "$repo_root"
printf 'CURRENT_BRANCH=%s\n' "$current_branch"
printf 'WORKTREE_PATH=%s\n' "$repo_root"
printf 'MAIN_WORKTREE_PATH=%s\n' "$main_wt_path"
printf 'IS_MAIN_WORKTREE=%s\n' "$is_main_worktree"
printf 'MAIN_BRANCH=%s\n' "$main_branch"
printf 'ALREADY_MERGED=%s\n' "$already_merged"

if [[ -n "$status" ]]; then
  echo "WORKING_TREE_CLEAN=false"
  echo "STATUS_BEGIN"
  printf '%s\n' "$status"
  echo "STATUS_END"
  echo "工作区存在未提交的修改，已停止。请先运行 commit-and-push 提交后再执行收尾。" >&2
  exit 1
fi

echo "WORKING_TREE_CLEAN=true"
