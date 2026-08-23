#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  cleanup.sh

合并推送成功后清理残留（在 dev worktree 目录内运行）：切到主 worktree，逐项
移除当前 dev worktree、删除远程 dev 分支、删除本地 dev 分支。
- git worktree remove：目录含未跟踪或修改文件（或已锁定）时 git 拒绝，
  报告残留，绝不 --force；
- git push origin --delete：远程分支已不存在时视为完成
  （REMOTE_BRANCH_DELETED=skipped-gone）；删除后 git remote prune origin
  清理过期的远程跟踪引用（失败不阻断），避免 git branch -d 误判；
- git branch -d：分支未合并或仍被 worktree 检出时保留并报告，绝不自动 -D。
单项失败不阻断整体流程，残留项全部列入 REMAINING 区段，脚本以 0 退出。
重复运行时已移除/已删除项视为完成（幂等）。

输出 KEY=VALUE 与区段标记：
  CURRENT_BRANCH、MAIN_WORKTREE_PATH、WORKTREE_PATH
  WORKTREE_REMOVED、LOCAL_BRANCH_DELETED、REMOTE_BRANCH_DELETED
  （取值 true/false；REMOTE_BRANCH_DELETED 另可取 skipped-gone）
  REMAINING_BEGIN/REMAINING_END   残留项列表（每行一项，含原因）
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

remaining=()

# 把命令输出折叠为单行（git 多行错误信息入残留报告时用）
collapse() {
  printf '%s' "$1" | tr '\n' ' '
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

# 主干分支：本仓库约定为 main（仅支持 main，见 Spec Out of Scope）
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

# 清理在主 worktree 内执行（避免移除当前所在 worktree）
cd "$main_wt_path"

# 1. 移除当前 dev worktree：git 原生保护，绝不 --force；
#    目录已不存在（重复运行或手工删除）时视为已移除
worktree_removed=false
if [[ ! -d "$repo_root" ]]; then
  worktree_removed=true
elif wt_remove_out="$(git worktree remove -- "$repo_root" 2>&1)"; then
  worktree_removed=true
else
  remaining+=("worktree ${repo_root}：$(collapse "$wt_remove_out")，未使用 --force")
fi

# 2. 删除远程 dev 分支：已不存在（ls-remote --exit-code=2）视为完成。
#    先删远程再删本地：git branch -d 相对 upstream 判定合并，若远程跟踪引用
#    滞后（本地领先远程但已合入 main），会误报 not fully merged。
remote_deleted=false
ls_code=0
git ls-remote --exit-code origin "refs/heads/$current_branch" >/dev/null 2>&1 || ls_code=$?
if [[ "$ls_code" -eq 0 ]]; then
  if push_del_out="$(git push origin --delete "$current_branch" 2>&1)"; then
    remote_deleted=true
  else
    remaining+=("远程分支 origin/${current_branch}：$(collapse "$push_del_out")")
  fi
elif [[ "$ls_code" -eq 2 ]]; then
  remote_deleted="skipped-gone"
else
  remaining+=("远程分支 origin/${current_branch}：无法确认远程状态（ls-remote 退出码 ${ls_code}）")
fi

# 清理过期的远程跟踪引用：删除远程分支后 refs/remotes/origin/<branch> 仍残留，
# 会让 git branch -d 误判「未完全合并」。prune 失败（如网络不可达）不阻断，
# 本地分支仍按 -d 判定，误判时保留并列入残留。
git remote prune origin >/dev/null 2>&1 || true

# 3. 删除本地 dev 分支：已合并才删除，绝不自动 -D；
#    分支已不存在（重复运行）时视为已删除
local_deleted=false
if ! git rev-parse -q --verify "refs/heads/$current_branch" >/dev/null 2>&1; then
  local_deleted=true
elif branch_del_out="$(git branch -d -- "$current_branch" 2>&1)"; then
  local_deleted=true
else
  remaining+=("本地分支 ${current_branch}：$(collapse "$branch_del_out")，未使用 -D")
fi

printf 'CURRENT_BRANCH=%s\n' "$current_branch"
printf 'MAIN_WORKTREE_PATH=%s\n' "$main_wt_path"
printf 'WORKTREE_PATH=%s\n' "$repo_root"
printf 'WORKTREE_REMOVED=%s\n' "$worktree_removed"
printf 'LOCAL_BRANCH_DELETED=%s\n' "$local_deleted"
printf 'REMOTE_BRANCH_DELETED=%s\n' "$remote_deleted"
echo "REMAINING_BEGIN"
if [[ "${#remaining[@]}" -gt 0 ]]; then
  printf '%s\n' ${remaining[@]+"${remaining[@]}"}
fi
echo "REMAINING_END"
exit 0
