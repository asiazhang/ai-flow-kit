---
name: finish-worktree
description: 在 dev worktree 内把当前 dev 分支以 --no-ff 合并进 main 并推送，合并推送成功后关闭最相关的关联 GitHub issue，并清理 worktree 与本地/远程 dev 分支（残留项不阻断、列入报告）；已合入时跳过合并，合并冲突或推送反复被拒时停止并报告，无法可靠识别关联 issue 时不关闭
disable-model-invocation: true
user-invocable: true
tools: Bash
---

## 目标

在当前 dev worktree 目录内执行收尾流程：把 dev 分支合并进 `main` 并推送，合并推送成功后关闭最相关的关联 GitHub issue，最后清理 worktree 与本地/远程 dev 分支。除安全边界外不停止等待用户。

**确认模式：全自动，无确认 gate。** 全程不请求用户确认（有意偏离 `clean-branches` 的删除前确认先例）：安全性由 git 原生保护（`worktree remove` 拒绝含未跟踪/修改文件的目录、`branch -d` 要求已合并）与 issue 识别保守规则（宁可不关、不要关错）兜底。仅在以下安全边界处停止：

- 工作区（dev worktree 或主 worktree）存在未提交修改——先运行 `commit-and-push` 提交后再执行；
- 合并产生冲突——报告冲突文件，不自动解决；
- 推送被拒且重试一次后仍被拒——停止，请人工处理；
- 无法可靠识别关联 issue 或查询状态失败——不关闭（防误关）。

任何一步停止时，最终报告说明停止点与原因，不自动继续。流程结束后输出六要素统一报告（见步骤 6）。

> **实现状态**：流程包含 **Preflight / Identify / Merge / Close / Cleanup / Report** 六个步骤。

命令中的 `<skill-dir>` 指本 Skill 所在目录。当前必须在 dev worktree 目录内运行。

### 1. Preflight：识别 worktree 与合并前状态

执行：

```bash
bash "<skill-dir>/scripts/preflight.sh"
```

脚本只读 Git 数据，不合并不推送。记录输出的 `CURRENT_BRANCH`、`WORKTREE_PATH`、`MAIN_WORKTREE_PATH`、`IS_MAIN_WORKTREE`、`MAIN_BRANCH`、`ALREADY_MERGED` 与工作区状态。

工作区存在未提交修改时脚本以非零状态停止并提示：先运行 `commit-and-push` 提交后再执行收尾，避免 WIP 混入主干。

**完成条件**：确认当前处于 dev worktree（非主 worktree）；当前分支已固定；工作区已提交干净；已记录分支是否已合入主干。

### 2. Identify：识别最相关的关联 issue

执行：

```bash
bash "<skill-dir>/scripts/extract-issue.sh"
```

脚本只读当前分支独有提交（相对 main）的提交信息，提取 issue 引用（`#N` / `Closes #N` / `Fixes #N`），输出候选列表：`CLOSES` 区段为带关闭关键词的引用，`CANDIDATES` 区段为全部引用。

结合会话上下文中确认的 worktree 关联 issue 号，与脚本输出互相校验，确定**仅一个**最相关的 issue 号：

- 提交信息含关闭关键词（如 `Closes #N`）时优先考虑；
- 会话确认的 issue 号与候选不一致、提取模糊或无法确认时，**选择不关闭**（宁可不关、不要关错）；
- 无候选且会话未确认 issue 时，跳过 Close 步骤。

**完成条件**：已确定待关闭的 issue 号，或明确决定跳过关闭。

### 3. Merge：同步主干、合并并推送

执行：

```bash
bash "<skill-dir>/scripts/merge-push.sh"
```

脚本自动定位 `main` 所在 worktree，执行 `git fetch` 刷新 `origin/main`；本地 `main` 落后远程时先合并 `origin/main`；随后以 `git merge --no-ff` 合并当前 dev 分支（保留分支上下文历史）；最后 `git push origin main`。

- 当前分支已合入主干（`ALREADY_MERGED=true`）时，脚本跳过 dev 合并（不创建空合并提交）；若本地主干落后远程，仍会同步并推送，保证远程最新——重复运行安全；
- 合并产生冲突时脚本停止并报告冲突文件，不自动解决，由用户处理；
- 推送被拒且本次尚未同步过远程主干时，脚本同步后重试一次；重试仍被拒则停止并报告。

记录输出的 `ALREADY_MERGED`、`MERGE_COMMIT`、`SYNCED` 与 `PUSHED`（推送状态）。

**`MERGE_COMMIT` 语义**：仅在未跳过 dev 合并时非空，值为最终推送的 `HEAD`（推送被拒重试时该哈希为同步合并提交，其历史包含 dev 合并）；跳过 dev 合并时为空。已合入但主干落后时仍会同步推送（产生新同步合并提交），此时 `MERGE_COMMIT` 仍为空——报告需如实转述 `SYNCED=true`，不说"未产生新提交"。

**完成条件**：`PUSHED=true` 且已记录 `MERGE_COMMIT`；未发生冲突或推送反复被拒。

### 4. Close：关闭关联 issue

仅当 Identify 已确定 issue 号、且 Merge 输出 `PUSHED=true` 与 `MERGE_COMMIT` 非空时执行：

```bash
MERGE_COMMIT=<merge-push 输出的 MERGE_COMMIT> bash "<skill-dir>/scripts/close-issue.sh" <issue-number>
```

脚本先从 `origin` remote 解析 repo（`owner/repo`），经 `GH_BIN`（默认 `gh`，可注入测试桩）查询 issue 状态：

- 已关闭（`CLOSED`）：跳过评论与关闭，输出 `SKIPPED=true`——重复执行幂等；
- 开放：先留评论注明合并提交哈希，再 `gh issue close`；
- 查询失败或无法确认状态：停止且不关闭（防误关）。

记录输出的 `ISSUE_NUMBER`、`REPO`、`ISSUE_STATE`、`COMMENTED`、`CLOSED`。

分支已合入（`ALREADY_MERGED=true`）时 Merge 不产生 dev 合并提交（`MERGE_COMMIT` 为空），无法在评论中注明 dev 合并提交哈希，此时**跳过 Close 步骤**并在最终报告说明（宁可不关、不要关错）。

**完成条件**：`CLOSED=true` 或 `SKIPPED=true`；未发生状态查询失败。

### 5. Cleanup：移除 worktree 并删除本地/远程 dev 分支

当 Merge 输出 `PUSHED=true` 时执行：

```bash
bash "<skill-dir>/scripts/cleanup.sh"
```

脚本在 dev worktree 目录内运行，切到主 worktree 后逐项清理：

- `git worktree remove` 移除当前 dev worktree；目录含未跟踪或修改文件（或已锁定）时 git 拒绝，脚本报告残留，**绝不 `--force`**；
- `git branch -d` 删除本地 dev 分支；分支未合并或仍被 worktree 检出时保留并报告，**绝不自动 `-D`**；
- `git push origin --delete` 删除远程 dev 分支；远程分支已不存在时视为完成（`REMOTE_BRANCH_DELETED=skipped-gone`）。

单项失败不阻断整体流程，残留项全部列入 `REMAINING` 区段，最终报告需逐项转述。重复运行幂等：已移除/已删除项视为完成，不产生虚假残留。

记录输出的 `WORKTREE_REMOVED`、`LOCAL_BRANCH_DELETED`、`REMOTE_BRANCH_DELETED` 与 `REMAINING` 残留项。

**完成条件**：worktree 已移除或残留原因已列入报告；本地分支已删除或保留原因已列入报告；远程分支已删除或已不存在；`REMAINING` 区段如实反映全部残留。

### 6. Report：汇总最终报告

收尾流程结束后，向用户输出统一最终报告，逐项转述以下**六要素**（数据来自各步骤输出的 `KEY=VALUE` 与区段标记，不凭空编造）：

1. **合并提交**：`merge-push.sh` 输出的 `MERGE_COMMIT`——未跳过 dev 合并时为最终推送的 `HEAD`（推送被拒重试时可能指向同步合并提交）；为空时说明"已合入主干，未创建 dev 合并提交"，若发生同步推送（`SYNCED=true`）如实说明主干已同步（可能产生同步合并提交）；
2. **推送状态**：`PUSHED=true`（推送成功才进入后续步骤；被拒重试时如实说明 `SYNCED` 与重试经过）；
3. **issue 关闭结果**：`close-issue.sh` 输出的 `CLOSED=true` 或 `SKIPPED=true`（已关闭幂等跳过）；未执行时说明原因（未识别到 issue、会话与提交信息不一致、`MERGE_COMMIT` 为空跳过 Close）；
4. **worktree 清理结果**：`cleanup.sh` 输出的 `WORKTREE_REMOVED`（true/false）；false 时转述残留原因与路径；
5. **本地/远程分支清理结果**：`LOCAL_BRANCH_DELETED`、`REMOTE_BRANCH_DELETED`（含 `skipped-gone`=远程分支已不存在视为完成）；false 时转述保留原因（未合并/仍被检出等）；
6. **残留项**：`REMAINING` 区段逐项转述；区段为空时报告"无残留"。

若流程在某一步停止（脚本非零退出），报告同步说明停止点、失败原因与下一步建议（如处理冲突、先运行 `commit-and-push`），不虚构后续步骤的结果。

**完成条件**：六要素全部如实汇报；残留项与停止点（如有）无一遗漏。
