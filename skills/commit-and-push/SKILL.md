---
name: commit-and-push
description: 自动将全部本地变更提交并推送当前分支，全程无需用户确认；推送被拒绝时自动 merge 后重试，仅在发现敏感内容或合并冲突时停止
disable-model-invocation: true
user-invocable: true
tools: Bash
---

## 目标

把全部本地变更自动形成一个 Conventional Commit 并推送到当前分支的 upstream。全程不做人工确认；推送被拒绝时自动 merge 远程变更后重试；只在发现敏感路径、凭证或合并冲突时停止并报告，由用户决定后续处理。

## 执行流程

### 1. Preflight：固定提交和推送目标

保持目标 Git 仓库为当前工作目录，使用当前已加载 Skill 的目录作为 `<skill-dir>`，执行：

```bash
bash "<skill-dir>/scripts/preflight.sh"
```

记录脚本输出的 `CURRENT_BRANCH`、`PUSH_REMOTE`、`PUSH_BRANCH`、`HAS_UPSTREAM`、`UPSTREAM_REF`、工作区状态和 `PENDING_COMMITS`。脚本只读 Git 数据，不提交或推送。

如果工作区干净且已有 upstream：

- `PENDING_COMMITS` 为空：报告“无变更”并停止；
- `PENDING_COMMITS` 非空：跳过暂存和提交步骤，直接进入推送步骤。

如果工作区干净且没有 upstream，不创建空提交。

**完成条件**：当前是具名分支；已固定唯一的推送目标；已记录工作区和 upstream 状态。

### 2. 暂存全部变更并做安全检查

先查看：

```bash
git status --short
git --no-pager diff --cached --name-status
git --no-pager diff --name-status
```

然后自动暂存全部变更：

```bash
git add -A
```

暂存完成后执行：

```bash
bash "<skill-dir>/scripts/inspect-staged.sh"
```

脚本扫描阻止路径并输出 `STAGED_NAME_STATUS` 和 `STAGED_DIFF` 区段。阻止路径包括环境文件、凭证相关文件、私钥、日志、依赖、构建产物、备份和临时文件。发现阻止路径时停止，要求用户先移出这些路径或明确处理。读取完整 `STAGED_DIFF`，如果发现 API Key、密码、Token、私钥或其他凭证，列出文件和位置并停止流程，要求用户先移除或明确处理。

**完成条件**：暂存区包含全部本地变更，不含阻止路径；staged diff 中未发现凭证。

### 3. 自动创建提交

基于 staged diff 生成 Conventional Commit：

- 格式：`<type>(<scope>): <subject>`；
- `type` 使用 `feat`、`fix`、`refactor`、`docs`、`style`、`test` 或 `chore`；
- 第一行 subject 不超过 50 个字符；
- 默认使用中文，除非用户要求英文。

在同一个 Bash 调用中把 `commit_message` 设为生成的实际第一行并校验非空和长度，再执行：

```bash
git commit -m "$commit_message"
```

提交失败或 Hook 修改工作区/暂存区时，停止自动重试，重新报告状态并等待用户处理。

**完成条件**：`git commit` 成功；提交后的状态已重新检查；没有把 Hook 新产生的修改误认为已提交内容。

### 4. 推送

提交完成后，在新的 Bash 调用中执行：

```bash
bash "<skill-dir>/scripts/resolve-push-target.sh"
```

脚本会重新解析当前分支和推送目标；有 upstream 时先执行 `git fetch <remote> <branch>`，再输出待推送提交、`REMOTE_AHEAD` 和远程领先的提交；没有 upstream 时输出首次推送所需的 `origin/<current_branch>`。记录 `CURRENT_BRANCH`、`PUSH_REMOTE`、`PUSH_BRANCH`、`PUSH_REMOTE_URL`、`PUSH_REFSPEC`、`HAS_UPSTREAM`、`IS_PROTECTED_BRANCH`、`REMOTE_AHEAD`、待推送提交和工作区状态。远程 URL 中的认证信息会被脚本遮蔽。

如果 `REMOTE_AHEAD=true`（远程有本地缺失的提交），先自动 merge 再推送：

1. 确认工作区没有未提交修改；如有，停止并报告；
2. 执行 `git pull --no-rebase`（merge，不 rebase）；
3. merge 产生冲突时，报告冲突文件并停止，不自动解决冲突；
4. merge 成功后继续推送。

目标一致后直接执行：

```bash
if [ -n "$upstream_ref" ]; then
  git push "$push_remote" "HEAD:$push_branch"
else
  git push -u "$push_remote" HEAD
fi
```

执行前在当前 Bash 调用中重新赋值并校验 `push_remote`、`push_branch` 和 `upstream_ref`，确保它们与脚本输出一致。不做人工确认，直接推送。

推送被远程拒绝且此前未执行过 merge 时（非 fast-forward，通常是 fetch 后远程又新增提交），按上述同样的 merge 流程处理并重试一次；重试仍被拒绝时停止并报告，不反复重试。

**完成条件**：推送命令成功，且推送目标与脚本解析的目标一致。

### 5. Verify：确认结果

执行：

```bash
bash "<skill-dir>/scripts/verify.sh"
```

`PENDING_COMMITS` 区段必须为空；如果不为空，报告验证失败。工作区仍有用户未提交的其他修改时，报告这些修改，但不要把它们描述为本次提交内容。

**完成条件**：存在 upstream，且 `PENDING_COMMITS` 为空。

### 6. Report：汇报

报告：

- 提交哈希和提交信息；
- 推送分支、远程地址和远程分支；
- 当前分支是否为 `main` 或 `master`；
- 已提交文件；
- Hook 产生或仍留在工作区的修改。
