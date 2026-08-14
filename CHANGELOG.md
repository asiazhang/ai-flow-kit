# Changelog

## [1.0.1] - 2026-08-14

### Added

- **Skills CLI 分组**：增加 `.claude-plugin/plugin.json`，在安装时将仓库中的 Skill 聚合为 `AI Flow Kit` 分组，支持批量选择

### Changed

- **安装说明**：补充多选和全选 Skill 的使用说明
- **开发与发布文档**：增加 Skill 集合清单的维护和校验步骤

## [1.0.0] - 2026-08-14

### Changed

- **安装方式**：从插件市场模式迁移到 Skills CLI，使用 `npx skills@latest add asiazhang/ai-flow-kit` 安装
- **Skill 目录**：将 Skill 统一迁移到仓库根目录的 `skills/` 目录

### Removed

- **插件市场**：移除 Claude Code、CodeBuddy 和 Codex CLI 的插件市场清单及插件配置

## [0.6.2] - 2026-07-14

## [0.6.1] - 2026-07-14

### Added

- **Skills**: 所有 Skill 增加 `user-invocable: true`，允许用户主动调用
