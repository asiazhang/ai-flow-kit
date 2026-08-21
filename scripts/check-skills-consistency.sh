#!/usr/bin/env bash
set -euo pipefail

# 校验 README 的 Skill 列表与 .claude-plugin/plugin.json 的 skills 数组一致。
# 供 run-release 的 postUpdateCommand 使用；只读，不修改文件。

repo_root="$(git rev-parse --show-toplevel)" || {
  echo "当前目录不在 Git 仓库内，已停止。" >&2
  exit 1
}
cd "$repo_root"

fail=0

# plugin.json 的 skills 数组（相对路径，如 ./skills/run-release）
plugin_skills="$(python3 -c "
import json
print('\n'.join(json.load(open('.claude-plugin/plugin.json')).get('skills', [])))
" 2>/dev/null || true)"

if [[ -z "$plugin_skills" ]]; then
  echo "FAIL .claude-plugin/plugin.json 缺少 skills 数组。" >&2
  exit 1
fi

# README 中 | `skill-name` | 开头的表格行，提取 skill 名
readme_skills="$(grep -oE '^\| `[a-z0-9-]+` \|' README.md | sed -E 's/^\| `([a-z0-9-]+)` \|/\1/' | sort -u)"

# plugin.json 中的 skill 名（取路径末段）
plugin_names="$(printf '%s\n' "$plugin_skills" | sed -E 's#^\./skills/##; s#/.*##' | sort -u)"

if [[ -z "$readme_skills" ]]; then
  echo "FAIL README.md 未找到 Skill 列表表格（\`| \`skill-name\` |\` 格式）。" >&2
  exit 1
fi

if [[ "$readme_skills" == "$plugin_names" ]]; then
  echo "OK  README Skill 列表与 plugin.json 的 skills 数组一致。"
else
  echo "FAIL README 与 plugin.json 的 Skill 列表不一致。"
  echo "  README:    ${readme_skills:-<空>}"
  echo "  plugin.json: ${plugin_names:-<空>}"
  exit 1
fi
