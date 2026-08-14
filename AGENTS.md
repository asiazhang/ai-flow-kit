# 仓库开发指南

本文件为 AI 编程助手提供本仓库的 Skill 开发规范。

## 项目概览

`ai-flow-kit` 是一个面向 AI 编程助手的 Skill 集合。用户通过 Skills CLI 从 GitHub 仓库安装 Skill：

```bash
npx skills@latest add asiazhang/ai-flow-kit
```

本仓库使用独立的 Skill 目录结构，并通过 `.claude-plugin/plugin.json` 提供 Skill 集合元数据。该文件只用于让 Skills CLI 将 Skill 聚合为一个可批量选择的分组，不使用插件市场清单或插件安装流程。

## 仓库结构

```text
ai-flow-kit/
├── skills/
│   └── <skill-name>/
│       └── SKILL.md
├── .claude-plugin/
│   └── plugin.json
├── docs/
│   └── guides/
├── CHANGELOG.md
├── README.md
└── AGENTS.md
```

## Skill 开发

### 目录与文件

每个 Skill 必须放在 `skills/<skill-name>/SKILL.md`。目录名使用小写 kebab-case，并与 frontmatter 中的 `name` 保持一致。

### Frontmatter

`SKILL.md` 使用 YAML frontmatter，至少包含：

```yaml
---
name: skill-name
description: 清晰描述 Skill 的用途和适用场景
---
```

按需补充 `user-invocable`、`disable-model-invocation` 和 `tools` 等字段。Skill 应保持与主流 AI 编程助手的兼容性。

`.claude-plugin/plugin.json` 中的 `skills` 数组必须列出所有可安装 Skill 的相对路径：

```json
{
  "name": "ai-flow-kit",
  "version": "1.0.1",
  "skills": [
    "./skills/branch-summary",
    "./skills/clean-branches",
    "./skills/commit-and-push",
    "./skills/new-branch"
  ]
}
```

新增或删除 Skill 时，必须同步更新这个数组和 README 中的 Skill 列表。

### 编写内容

- 先说明 Skill 的适用场景，再按顺序描述执行步骤
- 每个步骤都要有明确、可检查的完成条件
- 将必要的安全检查、失败处理和用户确认写入执行流程
- 命令、路径和参数使用代码格式
- 避免重复说明仓库中可以直接查到的信息
- 修改 Skill 后同步更新 README 中的 Skill 列表和描述（如有变化）

## 验证

提交前检查：

```bash
find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort
git diff --check
git status --short
```

确认每个 Skill 都存在 `SKILL.md`，frontmatter 可解析，且文档中的路径和命令与当前仓库结构一致。

## 版本与发布

面向用户的变更记录在 `CHANGELOG.md` 中维护。发布时遵循 [SemVer](https://semver.org/) 并创建对应的 Git tag；需要同步 `.claude-plugin/plugin.json` 中的版本号，不需要维护插件市场清单。

完整发布流程参见 [`docs/guides/release-process.md`](docs/guides/release-process.md)。
