#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  collect-changes.sh [--since-tag | --base <ref>]

输出自基线以来的变更事实（提交列表、变更文件、diff stat），
供判定版本号与编写 CHANGELOG 使用。只读，不输出 bump 建议。

--since-tag：以最近的 tag 为基线；没有 tag 时视为首版（基线为空）。
--base <ref>：显式指定基线。
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

base=""
if [[ "${1:-}" == "--since-tag" ]]; then
  base="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  shift
elif [[ "${1:-}" == "--base" ]]; then
  [[ $# -ge 2 ]] || { echo "--base 缺少值。" >&2; exit 2; }
  base="$2"
  shift 2
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

if [[ -n "$base" ]]; then
  echo "BASE_REF=$base"
  echo "COMMIT_COUNT=$(git rev-list --count "$base..HEAD" 2>/dev/null || echo 0)"
  echo "---COMMITS---"
  git log --oneline "$base..HEAD" 2>/dev/null || true
  echo "---FILES---"
  git diff --name-status "$base..HEAD" 2>/dev/null || true
  echo "---STAT---"
  git diff --stat "$base..HEAD" 2>/dev/null || true
else
  echo "BASE_REF="
  echo "COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo 0)"
  echo "---COMMITS---"
  git log --oneline 2>/dev/null || true
  echo "---FILES---"
  git ls-files
  echo "---STAT---"
  echo "(无基线，全部文件)"
fi
