# 版本发布流程

## 前置条件

- 当前分支为主干分支（`master` 或 `main`）
- 工作区干净，且已完成需要发布的变更
- 明确本次版本号，并遵循 [SemVer](https://semver.org/)：`MAJOR.MINOR.PATCH`

## 版本号决策

| 变更类型 | 版本递增 | 示例 |
|----------|---------|------|
| Bug 修复、内部重构、文档更新 | PATCH | 0.6.2 → 0.6.3 |
| 新增功能、新增 Skill（向后兼容） | MINOR | 0.6.2 → 0.7.0 |
| 破坏性变更（Skill 接口或行为不兼容） | MAJOR | 0.6.2 → 1.0.0 |

## 发布步骤

### 1. 同步主干分支

```bash
git checkout main
git pull --ff-only
```

确保当前位于主干分支且与远程同步。

### 2. 更新 CHANGELOG.md

1. 复制 `.changelog-template.md` 中 `## [VERSION]` 以下的内容到 `CHANGELOG.md` 顶部
2. 将 `<VERSION>` 替换为新版本号，将 `<YYYY-MM-DD>` 替换为发布日期
3. 删除不需要的分类小节，空分类不要保留
4. 填写各分类下的变更条目，仅记录对使用者可见的变更
5. 删除模板中的注释说明块

### 3. 检查 Skill 和集合清单

```bash
find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort
cat .claude-plugin/plugin.json
git diff --check
```

确认新增、修改或删除的 Skill 已同步反映在以下位置：

- `README.md` 的 Skill 列表
- `.claude-plugin/plugin.json` 的 `skills` 数组
- `CHANGELOG.md` 的发布条目（如属于用户可见变更）

### 4. 提交与标签

```bash
git add -A
git commit -m "release: X.Y.Z"
git tag vX.Y.Z
git push
git push --tags
```

### 5. 安装验证

在干净的测试项目中执行：

```bash
npx skills@latest add asiazhang/ai-flow-kit
```

确认新版本中的 Skill 能够被发现并正常安装。

## 回滚

若发布后发现问题：

1. 修复问题并递增 PATCH 版本号
2. 重新执行发布步骤
3. 不删除已推送的 tag，避免强制推送
