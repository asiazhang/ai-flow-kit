---
name: finish-worktree
description: 在 dev worktree 内识别 worktree 与合并前状态，把当前 dev 分支以 --no-ff 合并进 main 并推送；分支已合入时跳过合并，合并冲突或推送反复被拒时停止并报告，不自动解决
disable-model-invocation: true
user-invocable: true
tools: Bash
---

## 目标

在当前 dev worktree 目录内执行收尾流程的合并阶段：把 dev 分支合并进 `main` 并推送。除合并冲突、推送反复被拒等安全边界外不停止等待用户。

> **实现状态**：本骨架当前包含 **Preflight** 与 **Merge** 两个步骤；Identify/Close（关联 issue 关闭）与 Cleanup（worktree 与分支清理）步骤由后续任务补齐。

命令中的 `<skill-dir>` 指本 Skill 所在目录。当前必须在 dev worktree 目录内运行。

### 1. Preflight：识别 worktree 与合并前状态

执行：

```bash
bash "<skill-dir>/scripts/preflight.sh"
```

脚本只读 Git 数据，不合并不推送。记录输出的 `CURRENT_BRANCH`、`WORKTREE_PATH`、`MAIN_WORKTREE_PATH`、`IS_MAIN_WORKTREE`、`MAIN_BRANCH`、`ALREADY_MERGED` 与工作区状态。

工作区存在未提交修改时脚本以非零状态停止并提示：先运行 `commit-and-push` 提交后再执行收尾，避免 WIP 混入主干。

**完成条件**：确认当前处于 dev worktree（非主 worktree）；当前分支已固定；工作区已提交干净；已记录分支是否已合入主干。

### 2. Merge：同步主干、合并并推送

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
