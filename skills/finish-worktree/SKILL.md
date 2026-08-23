---
name: finish-worktree
description: 在 dev worktree 内把当前 dev 分支以 --no-ff 合并进 main 并推送，合并推送成功后关闭最相关的关联 GitHub issue，并清理 worktree 与本地/远程 dev 分支（残留项不阻断、列入报告）；已合入时跳过合并，合并冲突或推送反复被拒时停止并报告，无法可靠识别关联 issue 时不关闭
disable-model-invocation: true
user-invocable: true
tools: Bash
---

## 目标

在当前 dev worktree 目录内执行收尾流程：把 dev 分支合并进 `main` 并推送，合并推送成功后关闭最相关的关联 GitHub issue，最后清理 worktree 与本地/远程 dev 分支。除合并冲突、推送反复被拒、无法可靠识别 issue 等安全边界外不停止等待用户。

> **实现状态**：流程包含 **Preflight / Identify / Merge / Close / Cleanup** 五个步骤。

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

- 当前分支已合入主干（`ALREADY_MERGED=true`）时，脚本跳过合并（不创建空合并提交），仅同步并推送，保证远程最新——重复运行安全；
- 合并产生冲突时脚本停止并报告冲突文件，不自动解决，由用户处理；
- 推送被拒且本次尚未同步过远程主干时，脚本同步后重试一次；重试仍被拒则停止并报告。

记录输出的 `ALREADY_MERGED`、`MERGE_COMMIT`（合并提交哈希，跳过合并时为空）与 `PUSHED`（推送状态）。

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

分支已合入（`ALREADY_MERGED=true`）时 Merge 不产生新合并提交（`MERGE_COMMIT` 为空），无法在评论中注明合并提交哈希，此时**跳过 Close 步骤**并在最终报告说明（宁可不关、不要关错）。

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
