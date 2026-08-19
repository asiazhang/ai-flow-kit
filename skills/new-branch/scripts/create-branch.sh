#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  create-branch.sh \
    --description <kebab-case-description> \
    --branch <dev/branch-name> \
    --base <main|master>

重新检查仓库状态和分支冲突，刷新确认过的基础分支，执行 fast-forward，
然后创建并切换到新分支。
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

description=""
branch_name=""
base_branch=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --description)
      [[ $# -ge 2 ]] || { echo "--description 缺少值。" >&2; exit 2; }
      description="$2"
      shift 2
      ;;
    --branch)
      [[ $# -ge 2 ]] || { echo "--branch 缺少值。" >&2; exit 2; }
      branch_name="$2"
      shift 2
      ;;
    --base)
      [[ $# -ge 2 ]] || { echo "--base 缺少值。" >&2; exit 2; }
      base_branch="$2"
      shift 2
      ;;
    --)
      shift
      [[ $# -eq 0 ]] || { echo "不支持的位置参数：$1" >&2; exit 2; }
      ;;
    *)
      echo "未知参数：$1。使用 --help 查看用法。" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$description" || -z "$branch_name" || -z "$base_branch" ]]; then
  echo "--description、--branch 和 --base 都是必需参数。" >&2
  exit 2
fi

if [[ ! "$description" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "description 必须是小写 kebab-case。" >&2
  exit 2
fi
if [[ "${#description}" -gt 50 ]]; then
  echo "description 超过 50 个字符。" >&2
  exit 2
fi
if [[ "$branch_name" != "dev/$description" ]]; then
  echo "branch 必须等于 dev/<description>。" >&2
  exit 2
fi
if [[ "${#branch_name}" -gt 63 ]]; then
  echo "完整分支名超过 63 个字符。" >&2
  exit 2
fi
if [[ "$base_branch" != "main" && "$base_branch" != "master" ]]; then
  echo "base 必须是 main 或 master。" >&2
  exit 2
fi

git check-ref-format --branch "$branch_name" >/dev/null || {
  echo "生成的分支名不符合 Git ref 规则。" >&2
  exit 2
}

repo_root="$(git rev-parse --show-toplevel)" || {
  echo "当前目录不在 Git 仓库内，已停止。" >&2
  exit 1
}
cd "$repo_root"

stashed=false
if ! git diff --quiet HEAD; then
  git stash push -m "new-branch: 自动暂存，创建分支前" >/dev/null || {
    echo "自动暂存本地修改失败，已停止。" >&2
    exit 1
  }
  stashed=true
fi
# 未跟踪文件不参与 stash，会在切换分支时随工作区保留。

restore_stash() {
  if [[ "$stashed" == true ]]; then
    git stash pop || {
      echo "恢复暂存变更失败，stash 条目已保留，可用 git stash list 查看。" >&2
      return 1
    }
  fi
}

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

if git show-ref --verify --quiet "refs/heads/$branch_name" ||
   git ls-remote --exit-code --heads origin "$branch_name" >/dev/null 2>&1; then
  echo "$branch_name 已存在于本地或 origin，请换一个名称。" >&2
  exit 1
fi

git fetch --prune origin "$base_branch" >/dev/null || {
  echo "同步 origin/$base_branch 失败，已停止。" >&2
  restore_stash || true
  exit 1
}

if git show-ref --verify --quiet "refs/heads/$base_branch"; then
  base_source="local"
  git switch "$base_branch" || {
    echo "切换到 $base_branch 失败，已停止。" >&2
    restore_stash || true
    exit 1
  }
else
  base_source="origin"
  git switch -c "$base_branch" --track "origin/$base_branch" || {
    echo "无法从 origin/$base_branch 创建本地基础分支，已停止。" >&2
    restore_stash || true
    exit 1
  }
fi

git merge --ff-only "origin/$base_branch" || {
  echo "$base_branch 无法 fast-forward 到 origin/$base_branch，已停止。" >&2
  restore_stash || true
  exit 1
}

git switch -c "$branch_name" || {
  echo "创建 $branch_name 失败，已停止。" >&2
  restore_stash || true
  exit 1
}

stash_restored=false
if [[ "$stashed" == true ]]; then
  git stash pop || {
    echo "在新分支上恢复暂存变更时发生冲突，stash 条目已保留，可用 git stash list 查看，请手动解决。" >&2
    exit 1
  }
  stash_restored=true
fi

if [[ "$stashed" == false && -n "$(git diff --name-only HEAD)" ]]; then
  echo "创建分支后已跟踪文件出现修改，已停止并保留当前状态。" >&2
  git diff --name-only HEAD >&2
  exit 1
fi

printf 'REPO_ROOT=%s\n' "$repo_root"
printf 'BRANCH_NAME=%s\n' "$branch_name"
printf 'BASE_BRANCH=%s\n' "$base_branch"
printf 'BASE_SOURCE=%s\n' "$base_source"
printf 'CURRENT_BRANCH=%s\n' "$(git branch --show-current)"
printf 'STASH_USED=%s\n' "$stashed"
printf 'STASH_RESTORED=%s\n' "$stash_restored"
if [[ -z "$(git status --porcelain)" ]]; then
  echo "WORKING_TREE_CLEAN=true"
else
  echo "WORKING_TREE_CLEAN=false"
fi
