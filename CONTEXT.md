# CONTEXT.md — AI Flow Kit 领域术语表

本仓库的领域是面向 AI 编程助手的 Skill 集合。以下术语在 issue、文档、脚本输出与测试中统一使用；输出命名领域概念时使用本表定义，不漂移到同义词。

## 核心术语

| 术语 | 定义 | 避免用词 |
|---|---|---|
| **主干分支** | 仓库的集成目标分支，本仓库固定为 `main`（不支持 `master`，见 Spec Out of Scope）。dev 分支的功能最终以合并提交合入主干，并由 `finish-worktree` 推送 `origin/main` | 主分支、主线 |
| **dev 分支** | 从主干切出的功能开发分支，命名 `dev/<description>`（见 `new-branch` 约定）；通常以独立 worktree 检出，功能完成后由收尾流程合入主干并删除本地/远程分支 | 特性分支、feature 分支 |
| **worktree** | `git worktree` 管理的独立工作目录。主 worktree 检出 `main`（`MAIN_WORKTREE_PATH`）；dev worktree 检出 dev 分支（`WORKTREE_PATH`）。收尾流程在 dev worktree 目录内调用，清理在切到主 worktree 后执行 | 工作区、副本 |
| **收尾流程** | `finish-worktree` skill 执行的"合并主干 → 关闭关联 issue → 清理 worktree 与本地/远程分支"完整流程，含 Preflight / Identify / Merge / Close / Cleanup / Report 六步 | 收尾、清理流程 |
| **issue 关联** | dev 分支与 GitHub issue 的对应关系：由会话上下文确认的 issue 号与提交信息提取（`#N` / `Closes #N` / `Fixes #N`）互相校验；收尾时**仅关闭最相关的一个 issue**，无法可靠识别时不关闭（宁可不关、不要关错） | 关联 issue、对应 issue |

## 流程内派生概念

| 术语 | 定义 |
|---|---|
| **合并提交** | `git merge --no-ff` 产生的 merge commit（`MERGE_COMMIT`），保留 dev 分支上下文历史；分支已合入主干时为空 |
| **残留项** | 清理步骤中未完成的项（`REMAINING` 区段，如 worktree 含未跟踪文件、本地分支未合并、远程分支删除失败），单项失败不阻断整体流程，全部列入最终报告 |
| **已合入** | 当前 dev 分支是 `main`（或 `origin/main`）的祖先（`ALREADY_MERGED=true`），此时跳过 dev 合并，仅同步推送主干 |
