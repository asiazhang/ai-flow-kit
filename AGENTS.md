# 仓库开发指南

## 项目概览

`ai-flow-kit` 是一个面向 AI 编程助手的 Skill 集合。每个 Skill 是 `skills/` 下一个独立目录；`.claude-plugin/plugin.json` 仅用于让 Skills CLI 将 Skill 聚合为一个可批量选择的分组。

## Skill 开发

### 目录与文件

- 每个 Skill 放在 `skills/<skill-name>/SKILL.md`，目录名使用小写 kebab-case，并与 frontmatter 中的 `name` 保持一致。
- frontmatter 使用 YAML，至少包含 `name` 和 `description`（清晰描述 Skill 的用途和适用场景），按需补充 `user-invocable`、`disable-model-invocation`、`tools` 等字段。

### 编写内容

- 先说明 Skill 的适用场景，再按顺序描述执行步骤
- 每个步骤都要有明确、可检查的完成条件
- 将必要的安全检查、失败处理和用户确认写入执行流程

### 同步更新

新增或删除 Skill 时，同步更新 `.claude-plugin/plugin.json` 的 `skills` 数组和 README 中的 Skill 列表；修改 Skill 描述时同步更新 README。

## 验证

提交前检查：

```bash
find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort
git diff --check
git status --short
```

确认每个 Skill 都存在 `SKILL.md`、frontmatter 可解析，且 `plugin.json` 的 `skills` 数组与 `skills/` 目录一致。

## 版本与发布

面向用户的变更记录在 `CHANGELOG.md` 中维护。发布时遵循 [SemVer](https://semver.org/) 并创建对应的 Git tag，同步 `.claude-plugin/plugin.json` 中的版本号。

发布前先读 [`docs/guides/release-process.md`](docs/guides/release-process.md)，按其执行完整发布流程。
