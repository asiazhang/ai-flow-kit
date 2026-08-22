#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  preflight.sh --trunk <main|master>

发布前前置检查：当前分支是主干、工作区干净、与 origin 同步、无空白错误。
除 `git fetch --prune` 外只读；fetch 用于刷新远程跟踪引用以便同步比较。
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

trunk=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --trunk)
      [[ $# -ge 2 ]] || { echo "--trunk 缺少值。" >&2; exit 2; }
      trunk="$2"
      shift 2
      ;;
    *)
      echo "未知参数：$1。使用 --help 查看用法。" >&2
      exit 2
      ;;
  esac
done

repo_root="$(git rev-parse --show-toplevel)" || {
  echo "当前目录不在 Git 仓库内，已停止。" >&2
  exit 1
}
cd "$repo_root"

fail_count=0
pass_count=0
note() { echo "OK  $1"; pass_count=$((pass_count + 1)); }
warn() { echo "WARN  $1"; }
fail() { echo "FAIL  $1"; fail_count=$((fail_count + 1)); }

# --- 主干分支 ---
if [[ -n "$trunk" ]]; then
  current_branch="$(git branch --show-current)"
  if [[ "$current_branch" == "$trunk" ]]; then
    note "当前分支是主干：$current_branch"
  else
    fail "当前分支 $current_branch 不是主干 ${trunk}。"
  fi
else
  warn "未指定主干分支，跳过分支检查。"
fi

# --- 工作区 ---
if [[ -z "$(git status --porcelain)" ]]; then
  note "工作区干净。"
else
  fail "工作区有未提交修改，先提交或暂存。"
fi

# --- 与远程同步 ---
if git remote get-url origin >/dev/null 2>&1; then
  if git fetch --prune origin >/dev/null 2>&1; then
    local_head="$(git rev-parse HEAD)"
    remote_head="$(git rev-parse "origin/$(git branch --show-current)" 2>/dev/null || true)"
    if [[ -n "$remote_head" && "$local_head" == "$remote_head" ]]; then
      note "本仓库与 origin 同步。"
    elif [[ -n "$remote_head" ]]; then
      fail "本仓库落后或领先于 origin，先同步（git pull --ff-only）。"
    else
      warn "无法解析远程跟踪分支，跳过同步检查。"
    fi
  else
    warn "fetch origin 失败，跳过同步检查。"
  fi
else
  warn "没有 origin，跳过同步检查。"
fi

# --- 空白错误 ---
if git diff --check >/dev/null 2>&1; then
  note "无空白错误。"
else
  fail "存在空白错误（git diff --check 失败）。"
fi

echo "PREFLIGHT_SUMMARY=通过 $pass_count 项，未通过 $fail_count 项"
if [[ "$fail_count" -eq 0 ]]; then
  echo "PREFLIGHT_RESULT=PASS"
else
  echo "PREFLIGHT_RESULT=FAIL"
  echo "共 $fail_count 项未通过，先修复再继续发布。" >&2
  exit 1
fi
