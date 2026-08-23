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

## 测试

脚本行为由 `tests/` 下的 pytest 用例覆盖（每个用例在临时 Git 仓库中调用脚本并断言输出，见 `tests/conftest.py` 的 `Repo` fixture）。修改 Skill 脚本后运行：

```bash
uv run pytest
```

测试按 Skill 脚本一一对应：修改 `skills/<skill>/scripts/<name>.sh` 时，同步检查对应的 `tests/test_<name>.py` 是否需要更新。

GitHub Actions（`.github/workflows/ci.yml`）在 push/PR 上自动执行：bash 语法检查、测试套件、README 与 plugin.json 一致性校验。

## 版本与发布

面向用户的变更记录在 `CHANGELOG.md` 中维护。发布时遵循 [SemVer](https://semver.org/) 并创建对应的 Git tag，同步 `.claude-plugin/plugin.json` 中的版本号。

发布前先读 [`skills/run-release/SKILL.md`](skills/run-release/SKILL.md)，按其执行完整发布流程。

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues for this repo. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical roles map to same-named labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` + `docs/adr/`. See `docs/agents/domain.md`.
