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
| `commit-and-push` | 确认暂存、提交和推送范围后提交并推送当前分支 |
| `new-branch` | 确认分支名和基础分支后同步主干并创建开发分支 |

## 开发

Skill 定义在 `skills/<skill-name>/SKILL.md`。新增或修改 Skill 前，请参考 [AGENTS.md](./AGENTS.md) 中的开发规范。

## 发布

发布流程参见 [`docs/guides/release-process.md`](docs/guides/release-process.md)。
