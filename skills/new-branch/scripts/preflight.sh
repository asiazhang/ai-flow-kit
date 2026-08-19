#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  preflight.sh

确认仓库处于可切换状态：没有进行中的 Git 操作，并且 origin 可用。
工作区可以不为空，输出 WORKING_TREE_CLEAN 标记，脏工作区由后续步骤自动暂存。
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

working_tree_clean=true
if [[ -n "$(git status --porcelain)" ]]; then
  echo "工作区不干净，创建分支时会自动暂存并在新分支上恢复。" >&2
  working_tree_clean=false
fi

for operation in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD BISECT_LOG; do
  operation_path="$(git rev-parse --git-path "$operation")"
  if [[ -e "$operation_path" ]]; then
    echo "仓库存在进行中的 Git 操作：$operation，已停止。" >&2
    exit 1
  fi
done

for operation_path in \
  "$(git rev-parse --git-path rebase-merge)" \
  "$(git rev-parse --git-path rebase-apply)"
do
  if [[ -d "$operation_path" ]]; then
    echo "仓库存在进行中的 rebase，已停止。" >&2
    exit 1
  fi
done

git remote get-url origin >/dev/null 2>&1 || {
  echo "找不到 origin，无法同步基础分支。" >&2
  exit 1
}

printf 'REPO_ROOT=%s\n' "$repo_root"
if [[ "$working_tree_clean" == true ]]; then
  echo "WORKING_TREE_CLEAN=true"
else
  echo "WORKING_TREE_CLEAN=false"
fi
echo "GIT_OPERATION_IN_PROGRESS=false"
echo "ORIGIN_AVAILABLE=true"
