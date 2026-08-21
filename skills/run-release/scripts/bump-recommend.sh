#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  bump-recommend.sh [--since-tag | --base <ref>]

按约定式提交（Conventional Commits）规则扫描基线以来的提交，给出版本递增建议
（major / minor / patch）及判定依据（命中的提交列表）。只读，不修改文件。

判定优先级（从高到低）：
  major  任一提交含 BREAKING CHANGE（提交正文，或 "!" 标记如 feat!:/feat(scope)!:）
  minor  任一提交为 feat（feat:/feat(scope):）
  patch  其余约定式类型（fix/refactor/perf/docs/chore/build/ci/style/test/revert/release 等）
  无前缀 按 patch 保守处理，列入 MATCHED_UNTYPED 供确认时复核

输出（机器可读）：
  COMMIT_COUNT=<n>
  NO_CHANGES=<0|1>        1 表示基线以来没有提交，无需发布
  SUGGESTED_BUMP=<major|minor|patch>
  ---MATCHED_MAJOR--- / ---MATCHED_MINOR--- / ---MATCHED_PATCH--- / ---MATCHED_UNTYPED---
  各分类下的提交（<短哈希> <提交信息>），空区块表示无命中
  WARN ...                存在未识别前缀提交或 major 时的提醒

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
  hashes="$(git rev-list "$base..HEAD" 2>/dev/null || true)"
else
  hashes="$(git rev-list HEAD 2>/dev/null || true)"
fi

if [[ -z "$hashes" ]]; then
  echo "COMMIT_COUNT=0"
  echo "NO_CHANGES=1"
  echo "SUGGESTED_BUMP=patch"
  exit 0
fi

major_list=()
minor_list=()
patch_list=()
untyped_list=()

while IFS= read -r hash; do
  [[ -n "$hash" ]] || continue
  full="$(git log -1 --format=%B "$hash" 2>/dev/null || true)"
  subject="$(printf '%s\n' "$full" | sed -n '1p')"
  short="$(git rev-parse --short "$hash" 2>/dev/null || printf '%s' "$hash")"
  line="$short $subject"

  if printf '%s\n' "$full" | grep -qi 'breaking change' \
     || printf '%s\n' "$subject" | grep -qE '^[A-Za-z]+(\([^)]*\))?!:'; then
    major_list+=("$line")
  elif printf '%s\n' "$subject" | grep -qE '^feat([(]|:)'; then
    minor_list+=("$line")
  elif printf '%s\n' "$subject" | grep -qE '^(fix|refactor|perf|docs|chore|build|ci|style|test|revert|release)([(]|:)'; then
    patch_list+=("$line")
  else
    untyped_list+=("$line")
  fi
done <<<"$hashes"

count=$(( ${#major_list[@]} + ${#minor_list[@]} + ${#patch_list[@]} + ${#untyped_list[@]} ))
echo "COMMIT_COUNT=$count"
echo "NO_CHANGES=0"
if (( ${#major_list[@]} > 0 )); then
  suggested="major"
elif (( ${#minor_list[@]} > 0 )); then
  suggested="minor"
else
  suggested="patch"
fi
echo "SUGGESTED_BUMP=$suggested"

echo "---MATCHED_MAJOR---"
[[ ${#major_list[@]} -gt 0 ]] && printf '%s\n' "${major_list[@]}"
echo "---MATCHED_MINOR---"
[[ ${#minor_list[@]} -gt 0 ]] && printf '%s\n' "${minor_list[@]}"
echo "---MATCHED_PATCH---"
[[ ${#patch_list[@]} -gt 0 ]] && printf '%s\n' "${patch_list[@]}"
echo "---MATCHED_UNTYPED---"
[[ ${#untyped_list[@]} -gt 0 ]] && printf '%s\n' "${untyped_list[@]}"

if [[ ${#untyped_list[@]} -gt 0 ]]; then
  echo "WARN 存在未使用约定式提交前缀的提交，已按 patch 保守处理，可在步骤 5 确认时复核。"
fi
if [[ "$suggested" == "major" ]]; then
  echo "WARN 检测到破坏性变更（major），步骤 5 确认时请重点复核。"
fi
