#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  extract-issue.sh

从当前分支独有提交（相对主干 main）的提交信息中提取 issue 引用
（#N / Closes #N / Fixes #N），输出候选列表，作为关闭关联 issue 的识别依据。
脚本只读 Git 数据，不做任何写操作。

输出 KEY=VALUE 与区段标记：
  CURRENT_BRANCH、MAIN_BRANCH
  CLOSES_COUNT   带关闭关键词（close/fix/resolve 及其变体）的引用数（去重）
  CLOSES_BEGIN/CLOSES_END   关闭关键词引用列表（每行一个 issue 号）
  ISSUE_COUNT    全部引用数（去重）
  CANDIDATES_BEGIN/CANDIDATES_END   全部引用列表（每行一个 issue 号）

无引用时列表为空、计数为 0。脚本仅做信息收集，始终以 0 退出。
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

# 去重保序：stdin 每行一个数字，输出首次出现顺序的唯一数字
dedupe() {
  local seen=" "
  local n
  while IFS= read -r n; do
    [[ -z "$n" ]] && continue
    case "$seen" in
      *" $n "*) ;;
      *) seen="$seen$n "; printf '%s\n' "$n" ;;
    esac
  done
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

# 主干分支：本仓库约定为 main（refs/heads 优先，否则 origin/main）
main_branch="main"
if git rev-parse -q --verify "refs/heads/$main_branch" >/dev/null 2>&1; then
  main_ref="refs/heads/$main_branch"
elif git rev-parse -q --verify "refs/remotes/origin/$main_branch" >/dev/null 2>&1; then
  main_ref="refs/remotes/origin/$main_branch"
else
  main_ref=""
  main_branch=""
fi

# 当前分支独有提交的完整提交信息（含正文），取相对 main 的独有范围
commit_msgs=""
if [[ -n "$main_ref" ]]; then
  commit_msgs="$(git --no-pager log --format=%B "${main_ref}..HEAD")"
fi

# 从提交信息提取 issue 号列表：grep 模式命中后取数字，去重保序
#（-i 忽略大小写：Closes/Fixes/Resolves 等关键词大小写不敏感）
extract_numbers() {
  local pattern="$1"
  {
    printf '%s\n' "$commit_msgs" \
      | grep -oiE "$pattern" \
      | grep -oE '[0-9]+' \
      || true
  } | dedupe
}

# 带关闭关键词的引用（GitHub 自动关闭语法，大小写不敏感；词边界避免
# "prefix #3" 之类子串误命中 fix 等关键词，遵循宁可不关、不要关错）
closes_numbers="$(extract_numbers '[[:<:]](close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)[[:space:]]*#[0-9]+')"
# 全部引用（#N，含关闭关键词引用）
candidates="$(extract_numbers '#[0-9]+')"

closes_count="$(printf '%s\n' "$closes_numbers" | sed '/^$/d' | wc -l | tr -d '[:space:]')"
issue_count="$(printf '%s\n' "$candidates" | sed '/^$/d' | wc -l | tr -d '[:space:]')"

printf 'CURRENT_BRANCH=%s\n' "$current_branch"
printf 'MAIN_BRANCH=%s\n' "$main_branch"
printf 'CLOSES_COUNT=%s\n' "$closes_count"
echo "CLOSES_BEGIN"
printf '%s\n' "$closes_numbers"
echo "CLOSES_END"
printf 'ISSUE_COUNT=%s\n' "$issue_count"
echo "CANDIDATES_BEGIN"
printf '%s\n' "$candidates"
echo "CANDIDATES_END"
