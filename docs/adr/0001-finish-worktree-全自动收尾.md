# ADR-0001: finish-worktree 收尾流程采用全自动无确认模式

## 状态

已接受（2026-08-23，随 `finish-worktree` skill 1.3.0 发布落地）。

## 背景

`clean-branches` skill 建立了"删除前请求确认"的先例：删除前展示完整候选列表并请求用户确认，确认内容必须说明删除范围，用户拒绝时停止且不执行删除（见 `skills/clean-branches/SKILL.md` 的 Delete gate）。

`finish-worktree` 的定位是 dev worktree 内的全自动收尾——在 worktree 目录内一条命令完成"合并主干 → 关闭关联 issue → 清理 worktree 与分支"。若沿用删除前确认先例，流程会在每个删除动作前打断用户，与"全自动、无需切换目录、不遗漏步骤"的目标直接冲突。

同时，全自动删除存在真实风险：worktree 目录可能含未跟踪或修改文件、本地分支可能未完全合并、远程分支可能不存在、关联 issue 可能识别错误。放弃确认 gate 意味着这些风险必须由其他机制兜底。

## 决策

`finish-worktree` 收尾流程**全程无确认 gate**（有意偏离 `clean-branches` 的删除前确认先例）。安全性由三层机制兜底：

1. **git 原生保护**：`git worktree remove` 拒绝含未跟踪/修改文件或已锁定的目录；`git branch -d` 要求分支已合并；两者均**绝不使用 `--force` / `-D`**。删除前校验前置条件（preflight 校验工作区已提交干净、merge-push 校验主干 worktree 干净）。
2. **issue 识别保守规则**：仅关闭 AI 识别出的最相关一个 issue（会话确认与提交信息提取互相校验）；会话与提交信息不一致、提取模糊、或无法确认 issue 状态时不关闭（宁可不关、不要关错）；已关闭则幂等跳过。
3. **单项失败不阻断**：清理中单项失败（worktree 未移除、分支保留等）不中断整体流程，全部列入 `REMAINING` 区段与最终报告，由用户可见、可补做。

仅在以下安全边界处停止（停止即报告停止点与原因，不自动继续）：

- 工作区（dev worktree 或主干 worktree）存在未提交修改——提示先运行 `commit-and-push`；
- 合并产生冲突——报告冲突文件清单，不自动解决；
- 推送被拒且重试一次后仍被拒——停止，请人工处理；
- 无法可靠识别关联 issue 或查询状态失败——不关闭（防误关）。

## 后果

**正面**：

- 收尾流程在 worktree 目录内一条命令跑完，无需逐动作确认、无需切换目录；
- 删除安全边界由 git 原生保护保证，未提交内容与未合并分支不会被强制删除；
- 重复运行幂等：已合入跳过合并、已关闭跳过关闭、已删除项视为完成。

**代价/负面**：

- 与 `clean-branches` 的确认先例不一致，未来读者可能困惑——本文档即为此而记（spec Further Notes 明确要求）；
- 流程不会在中途询问用户，失败后残留项需用户在最终报告中自行发现并补做（无自动重试）；
- issue 关闭偏保守，可能漏关而不是误关（宁可不关、不要关错）。

## 参考

- GitHub issue #1（spec，含全部 User Stories 与 Implementation Decisions）
- `skills/finish-worktree/SKILL.md`（六步执行流程与完成条件）
- `skills/clean-branches/SKILL.md`（删除前确认先例，本决策的偏离对象）
- `CONTEXT.md`（术语表：主干分支、dev 分支、worktree、收尾流程、issue 关联）
