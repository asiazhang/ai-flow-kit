# 仓库开发指南

本文件为 AI 编程助手（Claude Code、CodeBuddy、Codex CLI 等）提供仓库结构与开发规范说明。

## 插件组件说明

- **Agents**：AI 子代理，定义在 `agents/<name>.md`，可被 commands 或其他代理调用
- **Skills**：AI 自动识别并调用的专业能力，定义在 `skills/<name>/SKILL.md`
- **Commands**：用户手动触发的斜杠命令（`/<plugin>:<command>`），定义在 `commands/<name>.md`
- **Hooks**：特定事件触发时自动执行的操作，定义在 `hooks/hooks.json`

## 版本管理

插件版本号定义在以下文件中，发版时需同步更新：

| 文件 | 字段 | 说明 |
|------|------|------|
| `plugins/ai-kit/.codebuddy-plugin/plugin.json` | `"version"` | CodeBuddy 插件版本号 |
| `plugins/ai-kit/.claude-plugin/plugin.json` | `"version"` | Claude Code 插件版本号 |
| `plugins/ai-kit/.codex-plugin/plugin.json` | `"version"` | Codex CLI 插件版本号 |
| `.codebuddy-plugin/marketplace.json` | `plugins[0].version` | CodeBuddy 市场版本号 |
| `.claude-plugin/marketplace.json` | `plugins[0].version` | Claude Code 市场版本号 |
| `.agents/plugins/marketplace.json` | `plugins[0].version` | Codex CLI 市场版本号 |

版本号遵循 [SemVer](https://semver.org/) 规范：`MAJOR.MINOR.PATCH`

- **PATCH**：Bug 修复、内部重构、文档更新
- **MINOR**：新增功能、新增命令、新增 Agent/Skill（向后兼容）
- **MAJOR**：破坏性变更（命令接口、Agent 行为、配置格式变动）

完整发布流程参见 [`docs/guides/release-process.md`](docs/guides/release-process.md)，包括 Changelog 更新、版本号同步、提交打标签等步骤。
