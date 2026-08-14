# Changelog

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
