# 版本发布流程

## 前置条件

- 当前分支为 `master`（版本发布必须在 master 分支上进行）
- 明确本次版本号（遵循 [SemVer](https://semver.org/)：MAJOR.MINOR.PATCH）

## 版本号决策

| 变更类型 | 版本递增 | 示例 |
|----------|---------|------|
| Bug 修复、内部重构、文档更新 | PATCH | 0.5.11 → 0.5.12 |
| 新增功能、新增命令、新增 Agent/Skill（向后兼容） | MINOR | 0.5.11 → 0.6.0 |
| 协议破坏性变更（命令接口、Agent 行为、配置格式变动） | MAJOR | 0.5.11 → 1.0.0 |

## 发布步骤

### 1. 切换到 master 分支

```bash
git checkout master
git pull
```

确保当前在 master 分支且与远程同步。

### 2. 更新 CHANGELOG.md

1. 复制 `.changelog-template.md` 中 `## [VERSION]` 以下的内容到 CHANGELOG.md 顶部
2. 将 `<VERSION>` 替换为新版本号，`<YYYY-MM-DD>` 替换为当天日期
3. 删除不需要的分类小节（空分类不要保留）
4. 填写各分类下的变更条目（仅记录对使用者可见的变更，内部重构等不写入）
5. 删除模板中的注释说明块

### 3. 更新版本号（6 处）

| # | 文件 | 字段 | 修改方式 |
|---|------|------|---------|
| 1 | `plugins/ai-kit/.codebuddy-plugin/plugin.json` | `"version"` | 改为 `"X.Y.Z"` |
| 2 | `plugins/ai-kit/.claude-plugin/plugin.json` | `"version"` | 改为 `"X.Y.Z"` |
| 3 | `plugins/ai-kit/.codex-plugin/plugin.json` | `"version"` | 改为 `"X.Y.Z"` |
| 4 | `.codebuddy-plugin/marketplace.json` | `plugins[0].version` | 改为 `"X.Y.Z"` |
| 5 | `.claude-plugin/marketplace.json` | `plugins[0].version` | 改为 `"X.Y.Z"` |
| 6 | `.agents/plugins/marketplace.json` | `plugins[0].version` | 改为 `"X.Y.Z"` |

### 4. 提交与标签

```bash
git add -A
git commit -m "release: X.Y.Z"
git tag vX.Y.Z
git push; git push --tags
```

> 注意：`git push` 和 `git push --tags` 使用 `;` 连接而非 `&&`，确保兼容 bash/fish/zsh。

### 5. 发布后确认

- [ ] 确认标签在远程仓库可见
- [ ] 通知团队成员新版本已发布

## 回滚

若发布后发现问题：

1. 修复问题，递增 PATCH 版本号
2. 重新执行发布步骤
3. 不删除已推送的 tag（避免强制推送）
