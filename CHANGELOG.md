# Changelog

## [Unreleased]

### Added

- **仓库**：新增 pytest 测试套件（`tests/`，通过 `uv run pytest` 运行，覆盖全部 Skill 脚本的返回值、输出区段与临时仓库场景）与 GitHub Actions CI（push/PR 自动执行 bash 语法检查、测试与 README/plugin.json 一致性校验）

### Fixed

- **CI**：修复 ShellCheck 警告——移除 `check-skills-consistency.sh` 中未使用的 `fail` 变量、精简 `inspect-staged.sh` 中被 `*secret*` 覆盖的冗余模式 `*/.secret*`；并去掉 ShellCheck 步骤的 `continue-on-error`，使其不再掩盖静态检查失败
- **CI**：升级 GitHub Actions 到最新版（`actions/checkout@v7`、`astral-sh/setup-uv@v10.0.1`），消除 Node.js 20 deprecation 告警（Node 24 runtime）

## [1.2.2] - 2026-08-22

### Fixed

- **`run-release` Skill**：修复 `detect-project.sh` 在 macOS BSD sed 下无法解析版本 tag（BRE `\+` 量词无效），改用 POSIX ERE（`sed -nE`）；`preflight.sh`、`verify-release.sh` 同步加固变量引用，toml 版本解析统一改用 ERE
- **各 Skill 脚本**：统一加固变量引用（`$var` → `${var}`）与数组展开（`${arr[@]+"${arr[@]}"}`），兼容 `set -u` 与空数组场景；`clean-branches` 的 `discover-gone.sh` 改为显式 `bash` 调用，避免依赖可执行位

## [1.2.1] - 2026-08-21

### Changed

- **`run-release` Skill**：减少人工介入——版本号改为按约定式提交自动判定（新增 `bump-recommend.sh`，支持 `BREAKING CHANGE`/`!`/`feat`/常规类型/无前缀提交）；提交与打标签等本地动作自动执行，仅 **push 前确认一次**；新增可选 `autoPush` 配置（默认 false），开启后自动推送、全程无确认

## [1.2.0] - 2026-08-21

### Added

- **`run-release` Skill**：新增发布 Skill，按 `docs/guides/release-process.md` 自动化发布流程——计算语义化版本号、更新 CHANGELOG/plugin.json/README、校验发布前置状态、提交并打标签推送；配套 `next-version.sh` 和 `verify-release.sh` 脚本

## [1.1.2] - 2026-08-19

### Fixed

- **`branch-summary` Skill**：修复输出格式漂移：核心目标只写一个最高层级目标（多主题分支提炼共同意图或选主要主题，不再用“同时/并”罗列）；移除报告中“未提交修改”提示及证据脚本的工作区状态输出；“变更原因与改进”条目固定加粗关键词开头；“关键技术点”约束为一句话，不罗列文件名、行数或 diff 统计

## [1.1.1] - 2026-08-19

### Fixed

- **`commit-and-push` Skill**：当前分支没有 upstream 且工作区干净时不再误报“无变更”，回退到远程默认分支计算未推送提交（新增 `PENDING_BASE` 输出），存在未推送提交时直接以 `git push -u` 发布分支

## [1.1.0] - 2026-08-19

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
