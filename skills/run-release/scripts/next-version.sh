#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  next-version.sh --current <X.Y.Z> --bump <major|minor|patch>

按语义化版本规则计算下一个版本号并输出。
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

current=""
bump=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --current)
      [[ $# -ge 2 ]] || { echo "--current 缺少值。" >&2; exit 2; }
      current="$2"
      shift 2
      ;;
    --bump)
      [[ $# -ge 2 ]] || { echo "--bump 缺少值。" >&2; exit 2; }
      bump="$2"
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

if [[ -z "$current" || -z "$bump" ]]; then
  echo "--current 和 --bump 都是必需参数。" >&2
  exit 2
fi

if [[ ! "$current" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "当前版本 $current 不是有效的语义化版本号 X.Y.Z。" >&2
  exit 2
fi
case "$bump" in
  major|minor|patch) ;;
  *)
    echo "--bump 必须是 major、minor 或 patch。" >&2
    exit 2
    ;;
esac

IFS='.' read -r major minor patch <<<"$current"
case "$bump" in
  major)
    major=$((major + 1))
    minor=0
    patch=0
    ;;
  minor)
    minor=$((minor + 1))
    patch=0
    ;;
  patch)
    patch=$((patch + 1))
    ;;
esac

printf '%d.%d.%d\n' "$major" "$minor" "$patch"
