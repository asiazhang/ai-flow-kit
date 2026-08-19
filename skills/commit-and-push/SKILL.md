---
name: commit-and-push
description: 将用户确认的本地变更提交，并在再次确认后推送当前分支；会产生本地提交和远程副作用
disable-model-invocation: true
user-invocable: true
tools: Bash, AskUserQuestion
---

## 目标

把用户确认的变更形成一个 Conventional Commit，并在 Push gate 中再次确认后推送。只处理确认范围，不替用户决定无关修改、敏感文件或 rebase 策略。

## 执行流程

### 1. Preflight：固定提交和推送目标

保持目标 Git 仓库为当前工作目录，使用当前已加载 Skill 的目录作为 `<skill-dir>`，执行：

```bash
bash "<skill-dir>/scripts/preflight.sh"
```

记录脚本输出的 `CURRENT_BRANCH`、`PUSH_REMOTE`、`PUSH_BRANCH`、`HAS_UPSTREAM`、`UPSTREAM_REF`、工作区状态和 `PENDING_COMMITS`。脚本只读 Git 数据，不提交或推送。

如果工作区干净且已有 upstream：

- `PENDING_COMMITS` 为空：报告“无变更”并停止；
- `PENDING_COMMITS` 非空：跳过 Scope gate 和 Commit gate，进入 Push gate。

如果工作区干净且没有 upstream，不创建空提交。

**完成条件**：当前是具名分支；已固定唯一的推送目标；已记录工作区和 upstream 状态。

### 2. Scope gate：确定暂存范围

先查看：

```bash
git status --short
git --no-pager diff --cached --name-status
git --no-pager diff --name-status
```

让用户确认待处理文件范围，再执行对应的暂存命令：

- 整个文件：`git add -- "$path"`；
- 混合修改：`git add -p -- "$path"`；
- 文件名通过参数传递，不按空格拆分路径；
- 已在暂存区的内容也属于待审查范围；
- 用户未确认的文件保持原状。

暂存完成后执行：

```bash
bash "<skill-dir>/scripts/inspect-staged.sh"
```

脚本扫描阻止路径并输出 `STAGED_NAME_STATUS` 和 `STAGED_DIFF` 区段。阻止路径包括环境文件、凭证相关文件、私钥、日志、依赖、构建产物、备份和临时文件。发现阻止路径时停止，要求用户先移出这些路径或明确处理。读取完整 `STAGED_DIFF`，如果发现 API Key、密码、Token、私钥或其他凭证，列出文件和位置并停止流程，要求用户先移除或明确处理。

向用户展示 staged 文件和完整 staged diff，请求 Scope gate 确认。用户拒绝时保留工作区和暂存区现状并停止。

**完成条件**：暂存区只包含用户确认的目标内容，不包含阻止路径；staged diff 已展示并获得确认。

### 3. Commit gate：确认并创建提交

基于 staged diff 生成 Conventional Commit：

- 格式：`<type>(<scope>): <subject>`；
- `type` 使用 `feat`、`fix`、`refactor`、`docs`、`style`、`test` 或 `chore`；
- 第一行 subject 不超过 50 个字符；
- 默认使用中文，除非用户要求英文。

展示提交信息和 staged diff，请求 Commit gate 确认。确认后，在同一个 Bash 调用中把 `commit_message` 设为用户确认的实际第一行并校验非空和长度，再执行：

```bash
git commit -m "$commit_message"
```

提交失败或 Hook 修改工作区/暂存区时，停止自动重试，重新报告状态并等待用户处理。

**完成条件**：`git commit` 成功；提交后的状态已重新检查；没有把 Hook 新产生的修改误认为已提交内容。

### 4. Push gate：确认远程副作用

提交完成后，在新的 Bash 调用中执行：

```bash
bash "<skill-dir>/scripts/resolve-push-target.sh"
```

脚本会重新解析当前分支和推送目标；有 upstream 时先执行 `git fetch <remote> <branch>`，再输出待推送提交；没有 upstream 时输出首次推送所需的 `origin/<current_branch>`。记录 `CURRENT_BRANCH`、`PUSH_REMOTE`、`PUSH_BRANCH`、`PUSH_REMOTE_URL`、`PUSH_REFSPEC`、`HAS_UPSTREAM`、`IS_PROTECTED_BRANCH`、待推送提交和工作区状态。远程 URL 中的认证信息会被脚本遮蔽。

向用户展示并确认：

- 当前分支；
- 远程地址和远程分支；
- 待推送提交；
- 是否首次设置 upstream；
- 当前分支是否为 `main` 或 `master`；
- 工作区中仍存在但未提交的其他修改。

用户确认后执行：

```bash
if [ -n "$upstream_ref" ]; then
  git push "$push_remote" "HEAD:$push_branch"
else
  git push -u "$push_remote" HEAD
fi
```

执行前在当前 Bash 调用中重新赋值并校验 `push_remote`、`push_branch` 和 `upstream_ref`，确保它们与 Push gate 输出一致。

用户拒绝时报告“提交已完成但尚未推送”，不回滚提交。远程拒绝推送时停止，不自动 merge 或 rebase；只有用户明确选择 rebase 后才继续，且 rebase 前重新确认工作区没有未提交修改。冲突时报告冲突文件并停止。

**完成条件**：推送命令成功，且推送目标与 Push gate 展示的目标一致。

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
- 已提交文件；
- 明确跳过的文件；
- 用户未确认、Hook 产生或仍留在工作区的修改。
