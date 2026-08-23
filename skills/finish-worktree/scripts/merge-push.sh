#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  merge-push.sh

在 dev worktree 目录内运行：同步主干、以 --no-ff 把当前 dev 分支合并进 main，
并推送 origin main。当前分支已合入主干时跳过合并（仅同步并推送，保证远程最新）。
推送被拒且本次尚未同步过远程主干时，同步后重试一次；重试仍被拒则停止。
合并冲突时停止并报告冲突文件，不自动解决。

输出 KEY=VALUE 与区段标记：ALREADY_MERGED、MERGE_COMMIT、SYNCED、PUSHED。
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

# 报告合并冲突：输出区段标记并停止，不自动解决
report_conflict() {
  local what="$1"
  echo "CONFLICTED=true"
  echo "CONFLICT_FILES_BEGIN"
  git diff --name-only --diff-filter=U
  echo "CONFLICT_FILES_END"
  echo "${what} 时发生冲突，已停止。冲突文件见 CONFLICT_FILES，请人工解决。" >&2
  exit 1
}

# 刷新远程主干跟踪引用，失败则停止
fetch_origin() {
  git fetch origin "$main_branch" >/dev/null 2>&1 || {
    echo "同步远程主干 origin/${main_branch} 失败，已停止。" >&2
    exit 1
  }
}

# 把本地主干同步到 origin/main（--no-ff），冲突则报告并停止
merge_sync() {
  if ! git merge --no-ff "origin/$main_branch" -m "merge: sync ${main_branch}"; then
    report_conflict "同步 ${main_branch}"
  fi
}

# 以 --no-ff 合并当前 dev 分支，冲突则报告并停止
merge_dev() {
  if ! git merge --no-ff "$current_branch" -m "merge: ${current_branch}"; then
    report_conflict "合并 ${current_branch}"
  fi
}

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

if [[ "$current_branch" == "main" ]]; then
  echo "当前已在主干分支，请在 dev worktree 目录内运行本脚本。" >&2
  exit 1
fi

# 主干分支：本仓库约定为 main
main_branch="main"

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
  echo "无法定位主干分支 ${main_branch} 的 worktree，已停止。" >&2
  exit 1
fi

cd "$main_wt_path"

wt_branch="$(git branch --show-current)"
if [[ "$wt_branch" != "$main_branch" ]]; then
  echo "主干 worktree（${main_wt_path}）当前检出 ${wt_branch} 而非 ${main_branch}，已停止。" >&2
  exit 1
fi

wt_status="$(git status --porcelain)"
if [[ -n "$wt_status" ]]; then
  echo "主干 worktree 工作区存在未提交修改，已停止。请先运行 commit-and-push 提交。" >&2
  exit 1
fi

fetch_origin

sync_merged=false

# 本地主干落后远程时先合并 origin/main
if ! git merge-base --is-ancestor "origin/$main_branch" HEAD 2>/dev/null; then
  merge_sync
  sync_merged=true
fi

# 检测当前 dev 分支是否已合入主干（重复运行安全：已合入则不创建空合并提交）
already_merged=false
if git merge-base --is-ancestor "$current_branch" "refs/heads/$main_branch" 2>/dev/null; then
  already_merged=true
fi

if [[ "$already_merged" == false ]]; then
  merge_dev
fi

# 推送 origin main；被拒且本次未同步过远程主干时，同步后重试一次
if ! git push origin "$main_branch"; then
  if [[ "$sync_merged" == false ]]; then
    echo "推送被拒，正在同步远程主干后重试一次..." >&2
    fetch_origin
    merge_sync
    sync_merged=true
    if ! git push origin "$main_branch"; then
      echo "重试推送仍被拒绝，已停止，请人工处理。" >&2
      exit 1
    fi
  else
    echo "推送被拒且本次已同步过远程主干，已停止，请人工处理。" >&2
    exit 1
  fi
fi

# 合并提交哈希：未跳过合并时取最终推送的 HEAD（含重试同步产生的提交）
merge_commit=""
if [[ "$already_merged" == false ]]; then
  merge_commit="$(git rev-parse HEAD)"
fi

printf 'CURRENT_BRANCH=%s\n' "$current_branch"
printf 'MAIN_BRANCH=%s\n' "$main_branch"
printf 'ALREADY_MERGED=%s\n' "$already_merged"
printf 'MERGE_COMMIT=%s\n' "$merge_commit"
printf 'SYNCED=%s\n' "$sync_merged"
printf 'PUSHED=true\n'
