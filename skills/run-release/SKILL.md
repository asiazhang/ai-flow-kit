---
name: run-release
description: 发布项目新版本：探测项目约定、计算语义化版本号、更新版本元数据与 CHANGELOG、校验发布前置状态、提交并打标签（不推送，留用户 review 后自行推送）
disable-model-invocation: true
user-invocable: true
tools: Bash, Write, AskUserQuestion
---

## 目标

把当前变更发布为新版本，适用于任意 Git 项目。通过 `detect-project.sh` 自动探测项目约定（当前版本、CHANGELOG 路径与样式、主干分支、tag 前缀），必要时用 `.run-release.json` 覆盖。发布关键动作（提交、打标签）停下确认；**不推送**，让用户在本地 review 后自行推送，留出修复窗口。

**版本模型**：git tag 是版本唯一真值——当前版本一律从最近 tag 读；版本文件（若有）只用于"写入"、不用于"读取"，且只在 `.run-release.json` 显式配置 `versionFiles` 时才更新与校验，不自动探测。

## 执行流程

命令中的 `<skill-dir>` 指本 Skill 所在目录。整个流程分为五个阶段：`Preflight` → `Gate` → `Action` → `Verify` → `Report`。

本 Skill 的附加文件按目录组织：`scripts/` 是可执行脚本（直接调用），`references/` 是附加文档（按需查阅），`assets/` 是静态模板。目录结构：

```
run-release/
├── SKILL.md                          # 元数据 + 指令
├── scripts/                          # 可执行代码
│   ├── detect-project.sh
│   ├── preflight.sh
│   ├── collect-changes.sh
│   ├── next-version.sh
│   └── verify-release.sh
├── references/                       # 附加文档
│   └── CONFIG.example.md             # .run-release.json 配置字段说明
└── assets/                           # 静态模板
    └── changelog-template.md         # CHANGELOG 条目模板
```

### 1. Preflight：探测约定并检查前置状态

执行：

```bash
bash "<skill-dir>/scripts/detect-project.sh"
```

脚本只读，输出 `REPO_ROOT`、`CURRENT_VERSION`、`VERSION_FILES`、`CHANGELOG`、`CHANGELOG_STYLE`、`TRUNK_BRANCH`、`TAG_PREFIX`、`TEST_COMMAND`、`POST_UPDATE_COMMAND`。这些输出是后续所有步骤的**唯一事实来源**；若根目录存在 `.run-release.json`，其字段在探测阶段合并覆盖（字段说明见 [references/CONFIG.example.md](references/CONFIG.example.md)）。

- `CURRENT_VERSION` 从最近 tag 读（tag 是唯一真值）；无 tag 视为首版 `0.0.0`。
- `VERSION_FILES` 是 `.run-release.json` 显式配置的版本文件列表（`路径:类型`），未配置则为空（版本只存在于 tag）。

若 `CHANGELOG` 为空（没有可识别的 CHANGELOG），停下询问用户：版本条目写到哪里，再继续。

然后执行前置检查：

```bash
bash "<skill-dir>/scripts/preflight.sh" --trunk '<主干分支>'
```

检查：当前分支是主干、工作区干净、与 origin 同步（含 `git fetch --prune`）、无空白错误。任何 `FAIL` 都先修复再重跑，直到 `PREFLIGHT_RESULT=PASS`。

**完成条件**：已固定唯一目标——当前版本（tag）、CHANGELOG 路径、主干分支、tag 前缀；`PREFLIGHT_RESULT=PASS`。

### 2. Gate：收集变更、确定版本号

执行：

```bash
bash "<skill-dir>/scripts/collect-changes.sh" --since-tag
```

脚本只读，输出自最近 tag 以来的变更事实（提交列表、变更文件、diff stat），不输出 bump 建议。agent 据此按语义化规则判定递增 `major`、`minor` 还是 `patch`（Bug 修复/内部重构/文档 → PATCH；新增功能/新增 Skill → MINOR；破坏性变更 → MAJOR），再计算目标版本：

```bash
bash "<skill-dir>/scripts/next-version.sh" --current '<当前版本>' --bump '<major|minor|patch>'
```

把目标版本号**连同判定依据**（变更事实摘要）交用户确认，用户拒绝则重新判定。

**完成条件**：已与用户确认目标版本号及判定依据，且它符合语义化版本规则。

### 3. Action：更新版本文件与 CHANGELOG

用 Edit 工具修改文件：

- **版本文件**（`VERSION_FILES`，`路径:类型`，可为空）：按类型改版本号——`json` 改 JSON 的 `"version"` 字段，`toml` 改 TOML 的 `version` 行，`text` 替换 `<VERSION>` 占位符。为空时**跳过本项**（版本只存在于 tag）。
- **CHANGELOG**（`CHANGELOG`）：条目格式以 [assets/changelog-template.md](assets/changelog-template.md) 为准（不探测项目自带模板）。`CHANGELOG_STYLE` 为 `unreleased` 时，把顶部 `## [Unreleased]` 改名为 `## [<目标版本>] - <当天日期>`；为 `top-insert` 时，在标题之后、现有条目之前插入新版本条目 `## [<目标版本>] - <当天日期>`。下面按本次对使用者可见的变更填写分类（Added / Changed / Deprecated / Removed / Fixed / Security），每类条目以 `- **<模块>**：<变更描述>` 格式编写，只保留有内容的分类。

如果版本文件或 CHANGELOG 需要更新但无法编辑（如二进制、锁定文件），停下报告，由用户处理。

若 `POST_UPDATE_COMMAND` 非空，在完成上述编辑后执行：

```bash
eval '<POST_UPDATE_COMMAND>'
```

失败则停下报告。

**完成条件**：`VERSION_FILES` 非空时其版本号等于目标版本（为空时无此要求）；CHANGELOG 顶部是目标版本条目，无占位符，无空分类；`POST_UPDATE_COMMAND` 已执行且通过。

### 4. Verify：校验

执行：

```bash
bash "<skill-dir>/scripts/verify-release.sh" --version '<目标版本>' \
  --version-files '<VERSION_FILES>' \
  --changelog '<CHANGELOG>' \
  --changelog-style '<unreleased|top-insert>' \
  --tag-prefix '<tag 前缀>' \
  --command '<TEST_COMMAND>'   # 可选，仅当 TEST_COMMAND 非空
```

脚本只读，检查：版本文件（若有）已更新、CHANGELOG 有目标版本条目且无占位符、目标 tag 尚未存在、无空白错误，可选用 `--command` 运行发布前命令。输出以 `OK`/`WARN`/`FAIL` 开头，最后输出 `VERIFY_RESULT`。任何 `FAIL` 都先修复再重跑，直到 `VERIFY_RESULT=PASS`。

**完成条件**：`VERIFY_RESULT=PASS`，且没有未处理的 `FAIL`；若传了 `--command`，发布前命令已通过。

### 5. Action：提交与打标签（不推送）

向用户确认要提交并打标签后，在**同一个** Bash 调用中执行（保持状态一致）：

```bash
git add -A
git commit -m "<提交信息>"
git tag "<tag 前缀><目标版本>"
```

提交信息默认 `release: <目标版本>`（对齐仓库既有提交历史；可让用户指定）。先提交、再打标签。**不执行 `git push`**，留给用户在 review 后自行推送。若提交或打标签失败，停止并报告，不自动重试。

**完成条件**：提交、打标签均成功；tag 名是 `<tag 前缀><目标版本>`。tag 本身即是版本记录。

### 6. Report：汇报

报告：目标版本号、`CHANGELOG` 新增条目的摘要、提交哈希、tag 名，并明确提示**本次未推送**，给出后续命令 `git push && git push --tags`；提示推送前发现问题可直接修复（新增提交、删除并重打本地 tag）。若本次变更新增了 Skill/功能或改了对外接口，提示"可在干净测试项目验证发布"。

**完成条件**：报告中包含以上各项。

## 失败与回滚

- 任一步骤失败：停止并报告当前状态，不自动回滚、不自动重试
- 由于不推送，发现问题时用户有本地修复窗口：未推送前可直接修复后重新提交、删除并重打本地 tag（`git tag -d <tag>` 再重新 `git tag`）
