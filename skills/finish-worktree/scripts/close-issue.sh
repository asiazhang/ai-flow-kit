#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  close-issue.sh <issue-number>

对指定 GitHub issue 留评论并关闭（经 GH_BIN 调用 gh，默认 gh）。
- repo 参数（owner/repo）从 origin remote URL 解析，不硬编码；
- 关闭前先查询 issue 状态，已关闭则跳过（幂等）；
- 关闭前留评论注明合并提交哈希（环境变量 MERGE_COMMIT）；
- 无法确认 issue 状态时不关闭（防误关）。

环境变量：
  GH_BIN         gh 可执行文件路径或命令名（默认 gh，可注入测试桩）
  MERGE_COMMIT   合并提交哈希，写入关闭评论（可空）

输出 KEY=VALUE：ISSUE_NUMBER、REPO、ISSUE_STATE、COMMENTED、CLOSED
（issue 已关闭时输出 SKIPPED=true 并以 0 退出）。
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 1 || "$1" =~ [^0-9] || "$1" -le 0 ]]; then
  echo "用法：close-issue.sh <issue-number>" >&2
  exit 2
fi
issue="$1"

GH_BIN="${GH_BIN:-gh}"
merge_commit="${MERGE_COMMIT:-}"

repo_root="$(git rev-parse --show-toplevel)" || {
  echo "当前目录不在 Git 仓库内，已停止。" >&2
  exit 1
}
cd "$repo_root"

# 经 GH_BIN 调用 gh issue 子命令（统一注入 GH_BIN / issue / repo）
gh_issue() {
  local verb="$1"
  shift
  "$GH_BIN" issue "$verb" "$issue" -R "$repo" "$@"
}

# repo 从 origin remote URL 解析（owner/repo）
origin_url="$(git remote get-url origin 2>/dev/null)" || {
  echo "无法读取 origin remote，已停止。" >&2
  exit 1
}
if [[ "$origin_url" == *"://"* ]]; then
  # https://host/owner/repo(.git) 或 ssh://git@host/owner/repo(.git)
  path="${origin_url#*://}"
  path="${path#*/}"
else
  # ssh 风格 git@host:owner/repo(.git)
  path="${origin_url#*:}"
fi
path="${path%.git}"
if [[ -z "$path" || "$path" == /* || "$path" != */* || "$path" == *".."* ]]; then
  echo "无法从 origin remote 解析 owner/repo（当前：${origin_url}），已停止。" >&2
  exit 1
fi
repo="${path%/}"

# 查询 issue 状态；失败或无法确认时不关闭（防误关）
view_out="$(gh_issue view --json state --jq '.state')" || {
  echo "查询 issue #${issue} 状态失败，已停止（防误关）。" >&2
  exit 1
}
state="$(printf '%s' "$view_out" | tr -d '[:space:]')"
if [[ -z "$state" ]]; then
  echo "无法确认 issue #${issue} 状态，已停止（防误关）。" >&2
  exit 1
fi

if [[ "$state" == "CLOSED" ]]; then
  printf 'ISSUE_NUMBER=%s\n' "$issue"
  printf 'REPO=%s\n' "$repo"
  printf 'ISSUE_STATE=%s\n' "$state"
  echo "SKIPPED=true"
  exit 0
fi

# 关闭前留评论注明合并提交哈希
if [[ -n "$merge_commit" ]]; then
  body="已通过 finish-worktree 收尾流程合并推送，合并提交：${merge_commit}"
else
  body="已通过 finish-worktree 收尾流程合并推送。"
fi
gh_issue comment --body "$body"

# 评论成功后才关闭
gh_issue close

printf 'ISSUE_NUMBER=%s\n' "$issue"
printf 'REPO=%s\n' "$repo"
printf 'ISSUE_STATE=%s\n' "$state"
printf 'COMMENTED=true\n'
printf 'CLOSED=true\n'
