# AI Flow Kit

> A collection of reusable AI workflow skills for coding agents.

## 简介

`ai-flow-kit` 提供一组可复用的 AI 工作流 Skill，帮助团队标准化分支管理、变更总结、提交推送等开发流程。

## 安装

使用 Skills CLI 安装：

```bash
npx skills@latest add asiazhang/ai-flow-kit
```

安装命令会从 GitHub 仓库获取可用 Skill，并引导你选择需要安装的 Skill 和目标 AI 编程助手。

仓库提供 `.claude-plugin/plugin.json` 作为 Skill 集合元数据，因此安装时会将这些 Skill 聚合为 `AI Flow Kit` 分组。进入分组后可使用空格选择多个 Skill，或直接选择分组完成全选。

## 可用 Skill

| Skill | 描述 |
|-------|------|
| `branch-summary` | 同步主干后分析当前分支的已提交变更，并总结修改意图 |
| `clean-branches` | 确认后安全清理远程已删除的本地跟踪分支 |
| `commit-and-push` | 自动提交全部本地变更并推送当前分支，无需确认；推送被拒时自动 merge 重试 |
| `finish-worktree` | 在 dev worktree 内把当前分支合并进 main 并推送（含同步远程主干与被拒重试），合并推送成功后关闭最相关的关联 GitHub issue，并清理 worktree 与本地/远程 dev 分支（残留项不阻断、列入报告）；已合入时跳过合并，冲突或推送反复被拒时停止，无法可靠识别 issue 时不关闭 |
| `new-branch` | 自动生成分支名并同步主干创建开发分支，无需确认；未提交修改自动暂存并在新分支恢复，未提供描述时询问一次 |
| `run-release` | 按发布流程发布新版本：按约定式提交自动判定版本号、更新 CHANGELOG/plugin.json、校验前置状态、提交并打标签（本地动作自动执行，仅 push 前确认一次；可配置 autoPush 跳过确认） |

## 开发

Skill 定义在 `skills/<skill-name>/SKILL.md`。新增或修改 Skill 前，请参考 [AGENTS.md](./AGENTS.md) 中的开发规范。

修改 Skill 脚本后运行 `uv run pytest` 执行测试套件（每个用例在临时 Git 仓库中验证脚本行为）。仓库通过 GitHub Actions 在 push/PR 上自动运行语法检查、测试与一致性校验。

## 发布

发布流程参见 [`skills/run-release/SKILL.md`](skills/run-release/SKILL.md)，使用 `run-release` Skill 执行。
