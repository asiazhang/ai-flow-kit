#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  inspect-staged.sh

检查暂存区中的阻止路径，并输出暂存文件、完整 staged diff。
发现阻止路径时以非零状态停止，不执行任何修改。
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

blocked_paths=()
staged_paths=()
while IFS= read -r -d '' path; do
  staged_paths+=("$path")
  case "$path" in
    .env|.env.*|*/.env|*/.env.*|*.pem|*.key|credentials*|*/credentials*|*secret*|*/.secret*|*.log|*/logs/*|node_modules/*|*/node_modules/*|dist/*|*/dist/*|*~|*.bak|*.swp)
      blocked_paths+=("$path")
      ;;
  esac
done < <(git diff --cached --name-only -z)

printf 'REPO_ROOT=%s\n' "$repo_root"
printf 'STAGED_FILE_COUNT=%s\n' "${#staged_paths[@]}"

if [[ "${#blocked_paths[@]}" -gt 0 ]]; then
  echo "BLOCKED_PATHS_BEGIN"
  printf '%s\n' "${blocked_paths[@]}"
  echo "BLOCKED_PATHS_END"
  echo "请先移出这些路径或明确处理后再继续。" >&2
  exit 3
fi

echo "BLOCKED_PATHS_BEGIN"
echo "BLOCKED_PATHS_END"
echo "STAGED_NAME_STATUS_BEGIN"
git --no-pager diff --cached --name-status
echo "STAGED_NAME_STATUS_END"
echo "STAGED_DIFF_BEGIN"
git --no-pager diff --cached
echo "STAGED_DIFF_END"
