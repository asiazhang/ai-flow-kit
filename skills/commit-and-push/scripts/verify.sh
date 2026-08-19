#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  verify.sh

输出推送后的工作区、upstream 和剩余待推送提交。
只有不存在待推送提交时才以成功状态结束。
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

status="$(git status --short --branch)"
upstream_ref="$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)" || {
  echo "当前分支没有 upstream，无法验证推送结果。" >&2
  exit 1
}
pending_commits="$(git --no-pager log "$upstream_ref..HEAD" --oneline)"

echo "STATUS_BEGIN"
printf '%s\n' "$status"
echo "STATUS_END"
printf 'UPSTREAM_REF=%s\n' "$upstream_ref"
echo "PENDING_COMMITS_BEGIN"
printf '%s\n' "$pending_commits"
echo "PENDING_COMMITS_END"

if [[ -n "$pending_commits" ]]; then
  echo "推送后仍有未推送提交，验证失败。" >&2
  exit 1
fi
