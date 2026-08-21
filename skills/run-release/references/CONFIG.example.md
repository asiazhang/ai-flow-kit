# run-release 配置示例

`run-release` 不依赖固定配置文件：它通过 `scripts/detect-project.sh` 自动探测项目约定。
如果自动探测的结果与项目实际约定不符，可以在仓库根目录创建 `.run-release.json` 覆盖。

**版本模型**：git tag 是版本唯一真值，当前版本一律从最近 tag 读，**不**从版本文件读。`versionFiles` 只是"发布时要同步写入版本号"的清单，属于可选增强——不配置即认为版本只存在于 tag。

```json
{
  "versionFiles": [
    ".claude-plugin/plugin.json",
    { "path": "VERSION.txt", "kind": "text" }
  ],
  "changelog": "CHANGELOG.md",
  "tagPrefix": "v",
  "trunkBranch": "main",
  "preReleaseCommand": "make check",
  "postUpdateCommand": "bash scripts/check-skills-consistency.sh",
  "autoPush": true
}
```

## 字段说明

| 字段 | 默认（自动探测） | 说明 |
|------|------------------|------|
| `versionFiles` | 无 | 发布时需同步写入版本号的文件列表；不配置则版本只存在于 tag |
| `changelog` | CHANGELOG.md / CHANGELOG.changelog.md / HISTORY.md / CHANGES.md | 版本条目写入的文件 |
| `tagPrefix` | `v`（或最近一个 tag 剥离尾部 X.Y.Z 后的前缀） | git tag 前缀 |
| `trunkBranch` | `main` 或 `master` | 发布要求所在的主干分支 |
| `preReleaseCommand` | 探测到的测试命令（npm test / pytest / cargo test / make test） | 编辑后校验阶段运行的命令，失败则停止 |
| `postUpdateCommand` | 无 | 编辑版本文件与 CHANGELOG 后执行的任意命令（如校验 README/清单一致性），失败则停止 |
| `autoPush` | `false` | 是否在提交并打标签后自动执行 `git push && git push --tags`（跳过人工确认）；默认 `false` 时仍会在 push 前确认一次

### `versionFiles` 的 `kind` 取值

| kind | 行为 |
|------|------|
| `json` | 修改 JSON 的 `"version"` 字段 |
| `toml` | 修改 TOML 的 `version` 行 |
| `text` | 替换 `<VERSION>` 占位符 |

`kind` 可省略，按文件扩展名推断：`.json` → `json`、`.toml` → `toml`、其余 → `text`。

## 说明

- 省略的字段使用自动探测结果；`versionFiles` 与 `changelog` 会被校验。
- 该配置是**可选**的：大多数项目（CHANGELOG.md + main 分支，版本只存在于 tag）无需配置即可直接使用。
- 配置文件不要求存在；不存在时 skill 完全依赖自动探测。
- CHANGELOG 条目格式固定使用 skill 内建模板 `skills/run-release/assets/changelog-template.md`，不探测项目自带模板。
- `autoPush` 默认关闭：提交与打标签自动执行，仅 push 前保留一次确认；需要 CI 一键发布时再开启。
