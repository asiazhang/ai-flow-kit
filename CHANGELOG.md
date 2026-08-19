# Changelog

## [Unreleased]

### Fixed

- **`branch-summary` Skill**：分支已通过 merge 提交合入主干后不再误报“没有已提交文件变更”，自动回退到合并前的主干作基准并输出 `BRANCH_MERGED`/`MERGE_COMMIT`；提交列表过滤同步主干产生的合并提交，避免噪音
- **`clean-branches` Skill**：使用机器可读的 Git ref 信息识别失效分支，默认安全删除并避免误删当前分支或未合并提交
- **`commit-and-push` Skill**：改用当前分支 upstream 判断未推送提交，增加暂存区凭证检查、混合修改处理和推送前确认，禁止自动 rebase
- **`new-branch` Skill**：增加工作区和分支名校验，修复主分支切换失败及 `origin/HEAD` 可能拉错分支的问题

### Changed

- **`branch-summary` Skill**：恢复“意图优先”规则并把摘要措辞改为痛点导向，强调解释“为什么要改”重于描述“改了什么”
- **执行流程统一**：四个 Skill 统一采用 `Preflight`、`Gate`、`Action`、`Verify` 和 `Report` 阶段，明确每一步的完成条件
- **交互边界收紧**：提交、推送、删除分支、切换基础分支和创建新分支前增加明确确认门
- **文档可执行性优化**：减少重复说明，固定变量作用域，明确未提交修改、远程目标和失败后的停止行为

## [1.0.2] - 2026-08-17

### Changed

- **`new-branch` Skill**：创建分支前先定位 Git 仓库根目录，支持从仓库子目录执行

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
