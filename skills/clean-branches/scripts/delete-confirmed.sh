#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  delete-confirmed.sh --expected-branch <branch> [--expected-branch <branch> ...]

重新刷新并发现失效分支。只有当前候选列表与所有 expected-branch 完全一致时，
才逐个执行安全删除 git branch -d；删除失败的分支会保留。
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

expected_branches=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --expected-branch)
      [[ $# -ge 2 && -n "$2" ]] || {
        echo "--expected-branch 需要一个非空分支名。" >&2
        exit 2
      }
      expected_branches+=("$2")
      shift 2
      ;;
    --)
      shift
      if [[ $# -gt 0 ]]; then
        echo "不支持的位置参数：$1" >&2
        exit 2
      fi
      ;;
    *)
      echo "未知参数：$1。使用 --help 查看用法。" >&2
      exit 2
      ;;
  esac
done

if [[ "${#expected_branches[@]}" -eq 0 ]]; then
  echo "至少需要一个 --expected-branch。" >&2
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
actual_output="$("$script_dir/discover-gone.sh")"
actual_branches=()
in_gone_branches=false
while IFS= read -r line; do
  if [[ "$line" == "GONE_BRANCHES_BEGIN" ]]; then
    in_gone_branches=true
  elif [[ "$line" == "GONE_BRANCHES_END" ]]; then
    in_gone_branches=false
  elif [[ "$in_gone_branches" == true && -n "$line" ]]; then
    actual_branches+=("$line")
  fi
done <<< "$actual_output"

expected_sorted="$(printf '%s\n' "${expected_branches[@]}" | LC_ALL=C sort)"
actual_sorted="$(printf '%s\n' "${actual_branches[@]}" | LC_ALL=C sort)"

if [[ "$expected_sorted" != "$actual_sorted" ]]; then
  echo "确认后的候选列表已变化，未执行任何删除。" >&2
  echo "EXPECTED_BRANCHES_BEGIN" >&2
  printf '%s\n' "${expected_branches[@]}" >&2
  echo "EXPECTED_BRANCHES_END" >&2
  echo "ACTUAL_BRANCHES_BEGIN" >&2
  printf '%s\n' "${actual_branches[@]}" >&2
  echo "ACTUAL_BRANCHES_END" >&2
  exit 3
fi

printf 'REPO_ROOT=%s\n' "$(
  printf '%s\n' "$actual_output" |
    sed -n 's/^REPO_ROOT=//p'
)"
printf 'CURRENT_BRANCH=%s\n' "$(
  printf '%s\n' "$actual_output" |
    sed -n 's/^CURRENT_BRANCH=//p'
)"

for branch_name in "${expected_branches[@]}"; do
  if delete_output="$(git branch -d -- "$branch_name" 2>&1)"; then
    echo "RESULT=deleted"
    printf 'BRANCH=%s\n' "$branch_name"
  else
    echo "RESULT=retained"
    printf 'BRANCH=%s\n' "$branch_name"
    echo "REASON_BEGIN"
    printf '%s\n' "$delete_output"
    echo "REASON_END"
  fi
done

echo "VERIFY_BEGIN"
git for-each-ref \
  --format='%(refname:short)%09%(upstream:track)' \
  refs/heads/
echo "VERIFY_CURRENT_BRANCH=$(git branch --show-current)"
echo "VERIFY_END"
