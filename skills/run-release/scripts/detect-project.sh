#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
用法：
  detect-project.sh

探测项目发布相关约定：当前版本（从最近 tag 读）、CHANGELOG 路径与样式、
主干分支、git tag 前缀、可选版本文件列表。只读，不修改任何文件。

版本读取：一律从最近的语义化版本 tag 推导，tag 是版本唯一真值；无 tag 视为
首版（0.0.0）。版本文件（若有）只用于“写入”，不用于“读取”，且只在
.run-release.json 显式配置 versionFiles 时才生效，不自动探测。
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

# --- 读取 .run-release.json（可选，只读一次，作为配置来源） ---
cfg_version_files=""; cfg_changelog=""; cfg_tag_prefix=""; cfg_trunk=""; cfg_pre_cmd=""; cfg_post_cmd=""
if [[ -f .run-release.json ]]; then
  cfg="$(python3 - <<'PY'
import json
d = json.load(open('.run-release.json'))
def s(k):
    v = d.get(k)
    return v if isinstance(v, str) else ''
def version_files():
    out = []
    for e in (d.get('versionFiles') or []):
        if isinstance(e, str):
            path, kind = e, ''
        elif isinstance(e, dict) and e.get('path'):
            path, kind = str(e['path']), str(e.get('kind', ''))
        else:
            continue
        kind = kind.strip().rstrip(':')
        if kind in ('json', 'json:version'):
            kind = 'json'
        elif kind in ('toml', 'toml:version'):
            kind = 'toml'
        elif kind in ('text', 'text:VERSION'):
            kind = 'text'
        else:
            # 按扩展名推断
            kind = 'json' if path.endswith('.json') else ('toml' if path.endswith('.toml') else 'text')
        out.append(path + ':' + kind)
    return ' '.join(out)
print('cfg_version_files=%r' % version_files())
print('cfg_changelog=%r' % s('changelog'))
print('cfg_tag_prefix=%r' % s('tagPrefix'))
print('cfg_trunk=%r' % s('trunkBranch'))
print('cfg_pre_cmd=%r' % s('preReleaseCommand'))
print('cfg_post_cmd=%r' % s('postUpdateCommand'))
PY
)"
  eval "$cfg"
fi

# --- 当前版本：从最近 tag 读（tag 是唯一真值） ---
current_version=""
tag_prefix=""
recent_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$recent_tag" ]]; then
  v="$(printf '%s' "$recent_tag" | sed -n 's/.*\([0-9]\+\.[0-9]\+\.[0-9]\+\).*/\1/p')"
  if [[ -n "$v" ]]; then
    current_version="$v"
    tag_prefix="$(printf '%s' "$recent_tag" | sed -E 's/[0-9]+\.[0-9]+\.[0-9]+$//')"
  fi
fi
# 无 tag 或 tag 不含语义化版本：视为首版
if [[ -z "$current_version" ]]; then
  current_version="0.0.0"
fi

# --- tag 前缀：配置 > 从 tag 剥离 > 默认 v ---
if [[ -n "$cfg_tag_prefix" ]]; then
  tag_prefix="$cfg_tag_prefix"
elif [[ -z "$tag_prefix" ]]; then
  tag_prefix="v"
fi

# --- CHANGELOG 探测 ---
changelog=""
if [[ -n "$cfg_changelog" ]]; then
  changelog="$cfg_changelog"
else
  for cand in CHANGELOG.md CHANGELOG.changelog.md HISTORY.md CHANGES.md; do
    if [[ -f "$cand" ]]; then changelog="$cand"; break; fi
  done
fi

# changelog 为空时保持 none（SKILL.md 步骤 1 要求停下询问用户），不自行回退到 top-insert
changelog_style="none"
if [[ -n "$changelog" && -f "$changelog" ]]; then
  if grep -q '^## \[Unreleased\]' "$changelog"; then
    changelog_style="unreleased"
  else
    changelog_style="top-insert"
  fi
fi

# --- 主干分支探测 ---
trunk_branch=""
if [[ -n "$cfg_trunk" ]]; then
  trunk_branch="$cfg_trunk"
elif git show-ref --verify --quiet refs/heads/main 2>/dev/null; then
  trunk_branch="main"
elif git show-ref --verify --quiet refs/heads/master 2>/dev/null; then
  trunk_branch="master"
fi

# --- 发布前命令探测 ---
test_command=""
if [[ -n "$cfg_pre_cmd" ]]; then
  test_command="$cfg_pre_cmd"
elif [[ -f package.json ]] && grep -q '"test"' package.json; then
  test_command="npm test"
elif [[ -f pyproject.toml ]] && grep -q 'pytest' pyproject.toml; then
  test_command="pytest"
elif [[ -f Cargo.toml ]] && grep -q '\[\[test\]\]' Cargo.toml; then
  test_command="cargo test"
elif [[ -f Makefile ]] && grep -q '^test:' Makefile; then
  test_command="make test"
fi

post_update_command="$cfg_post_cmd"

printf 'REPO_ROOT=%s\n' "$repo_root"
printf 'CURRENT_VERSION=%s\n' "$current_version"
printf 'VERSION_FILES=%s\n' "$cfg_version_files"
printf 'CHANGELOG=%s\n' "$changelog"
printf 'CHANGELOG_STYLE=%s\n' "$changelog_style"
printf 'TRUNK_BRANCH=%s\n' "$trunk_branch"
printf 'TAG_PREFIX=%s\n' "$tag_prefix"
printf 'TEST_COMMAND=%s\n' "$test_command"
printf 'POST_UPDATE_COMMAND=%s\n' "$post_update_command"
