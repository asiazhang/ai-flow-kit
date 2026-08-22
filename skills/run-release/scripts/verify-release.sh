#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  verify-release.sh --version <X.Y.Z> [选项]

编辑后校验发布状态：版本文件（若有）已更新到目标版本、CHANGELOG 有目标版本条目
且无占位符、目标 tag 尚未存在、文件无空白错误。可选用 --command 执行发布前命令。
只读，不修改文件（除 --command 外）。所有事实由调用方以参数传入，本脚本不自行探测。

选项：
  --version-files <路径:类型 ...>    可选版本文件列表（.run-release.json 的 versionFiles，空则跳过）
  --changelog <路径>                  CHANGELOG 路径
  --changelog-style <unreleased|top-insert>
  --tag-prefix <前缀>                 默认 v
  --command <命令>                    可选发布前命令
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

version=""; version_files=""; changelog=""; changelog_style="top-insert"; tag_prefix="v"; pre_command=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      [[ $# -ge 2 ]] || { echo "--version 缺少值。" >&2; exit 2; }
      version="$2"; shift 2 ;;
    --version-files)
      [[ $# -ge 2 ]] || { echo "--version-files 缺少值。" >&2; exit 2; }
      version_files="$2"; shift 2 ;;
    --changelog)
      [[ $# -ge 2 ]] || { echo "--changelog 缺少值。" >&2; exit 2; }
      changelog="$2"; shift 2 ;;
    --changelog-style)
      [[ $# -ge 2 ]] || { echo "--changelog-style 缺少值。" >&2; exit 2; }
      changelog_style="$2"; shift 2 ;;
    --tag-prefix)
      [[ $# -ge 2 ]] || { echo "--tag-prefix 缺少值。" >&2; exit 2; }
      tag_prefix="$2"; shift 2 ;;
    --command)
      [[ $# -ge 2 ]] || { echo "--command 缺少值。" >&2; exit 2; }
      pre_command="$2"; shift 2 ;;
    *)
      echo "未知参数：$1。使用 --help 查看用法。" >&2
      exit 2 ;;
  esac
done

if [[ -z "$version" ]]; then
  echo "--version 是必需参数。" >&2
  exit 2
fi
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "版本 $version 不是有效的语义化版本号 X.Y.Z。" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)" || {
  echo "当前目录不在 Git 仓库内，已停止。" >&2
  exit 1
}
cd "$repo_root"

file_version() {
  local f="$1" k="${2:-}"
  if [[ -z "$k" ]]; then
    case "$f" in
      *.json) k="json" ;;
      *.toml) k="toml" ;;
      *)      k="text" ;;
    esac
  fi
  case "$k" in
    json) python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('version',''))" "$f" 2>/dev/null || true ;;
    toml) grep -m1 '^version' "$f" 2>/dev/null | sed -E 's/.*=[[:space:]]*"?([0-9][0-9.]*)"?.*/\1/' || true ;;
    *)    grep -oE '[0-9]+\.[0-9]+\.[0-9]+' "$f" 2>/dev/null | head -n1 || true ;;
  esac
}

fail_count=0
pass_count=0
note() { echo "OK  $1"; pass_count=$((pass_count + 1)); }
warn() { echo "WARN  $1"; }
fail() { echo "FAIL  $1"; fail_count=$((fail_count + 1)); }

# --- 版本文件（opt-in，来自 .run-release.json 的 versionFiles） ---
if [[ -n "$version_files" ]]; then
  for entry in $version_files; do
    [[ -n "$entry" ]] || continue
    path="${entry%:*}"; kind="${entry#*:}"
    cur="$(file_version "$path" "$kind")"
    if [[ -n "$cur" && "$cur" == "$version" ]]; then
      note "$path 已含版本 ${version}。"
    else
      fail "${path}（${cur:-未识别}）与目标版本 $version 不一致。"
    fi
  done
else
  note "未配置版本文件，版本只存在于 git tag，跳过版本文件检查。"
fi

# --- CHANGELOG ---
if [[ -n "$changelog" && -f "$changelog" ]]; then
  if grep -q "^## \[$version\] - " "$changelog"; then
    note "$changelog 已有版本 $version 条目。"
  else
    fail "$changelog 没有版本为 $version 的条目。"
  fi
  if [[ "$changelog_style" == "unreleased" ]] && grep -q '^## \[Unreleased\]' "$changelog"; then
    fail "$changelog 顶部仍保留 [Unreleased]，未改名为目标版本。"
  fi
  if head -n 60 "$changelog" | grep -qE '<(VERSION|YYYY-MM-DD)>'; then
    fail "$changelog 顶部存在未替换的模板占位符 <VERSION> 或 <YYYY-MM-DD>。"
  fi
else
  warn "未找到 CHANGELOG，跳过 CHANGELOG 检查。"
fi

# --- 目标 tag 冲突 ---
if [[ -n "$version" ]]; then
  tag="${tag_prefix}${version}"
  if [[ -n "$(git tag --list "$tag")" ]]; then
    fail "tag $tag 已存在，目标版本可能已发布。"
  else
    note "目标 tag $tag 尚不存在。"
  fi
fi

# --- 空白错误 ---
if git diff --check >/dev/null 2>&1; then
  note "无空白错误。"
else
  fail "存在空白错误（git diff --check 失败）。"
fi

# --- 发布前命令（--command） ---
if [[ -n "$pre_command" ]]; then
  echo "RUN_COMMAND=$pre_command"
  if eval "$pre_command" >/dev/null 2>&1; then
    note "发布前命令通过：$pre_command"
  else
    fail "发布前命令失败：$pre_command"
  fi
fi

echo "VERIFY_SUMMARY=通过 $pass_count 项，未通过 $fail_count 项"
if [[ "$fail_count" -eq 0 ]]; then
  echo "VERIFY_RESULT=PASS"
else
  echo "VERIFY_RESULT=FAIL"
  echo "共 $fail_count 项未通过，先修复再继续发布。" >&2
  exit 1
fi
