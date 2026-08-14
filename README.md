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

## 可用 Skill

| Skill | 描述 |
|-------|------|
| `branch-summary` | 分析当前 Git 分支相对主干分支的变更，并总结修改原因 |
| `clean-branches` | 检查并清理远程已删除的本地失效分支 |
| `commit-and-push` | 暂存更改、生成提交信息并推送到远程仓库 |
| `new-branch` | 将中文特性描述转换为英文分支名，并创建开发分支 |

## 开发

Skill 定义在 `skills/<skill-name>/SKILL.md`。新增或修改 Skill 前，请参考 [AGENTS.md](./AGENTS.md) 中的开发规范。

## 发布

发布流程参见 [`docs/guides/release-process.md`](docs/guides/release-process.md)。
