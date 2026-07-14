# Changelog

本文件记录 AI Flow Kit 的所有版本变更，遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/) 规范，版本号遵循 [SemVer](https://semver.org/)。

## [0.6.0] - 2026-07-14

### Changed

- **技能架构**：将 Agents 和 Commands 统一迁移为 Skills-only 架构，简化插件能力模型

### Removed

- **refine-requirements Skill**：移除 `refine-requirements` 功能（需求完善 Agent）

## [0.5.15] - 2026-07-13

### Removed

- **new-worktree Agent/Command/Skill**：移除 `new-worktree` 功能（创建 git worktree 和开发分支），长期未使用

## [0.5.14] - 2026-05-18

### Changed

- **branch-summary Agent**：强化输出格式约束，明确三段式结构（核心目标 / 变更原因与改进 / 关键技术点）为强制要求，禁止省略、调换顺序或添加额外段落；统一标题名称，修正示例中"主要涉及"与规范不一致的问题；将"避免长段文字"细化为"禁止连续超过两行的非结构化段落"。

## [0.5.13] - 2026-05-14

### Added

- 新增 Codex CLI 插件支持（`.codex-plugin/plugin.json` 及市场清单 `.agents/plugins/marketplace.json`）

## [0.5.12] - 2026-05-14

### Removed

- 移除 `upload.sh` 上传脚本

## [0.5.11] - 2026-05-14

### Added

- 初始化发布流程，新增 `docs/guides/release-process.md` 和 `.changelog-template.md`
