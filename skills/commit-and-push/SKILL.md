---
name: commit-and-push
description: 自动提交全部本地变更并推送当前分支，无需确认；推送被拒时自动 merge 重试，仅在发现敏感内容或合并冲突时停止
disable-model-invocation: true
user-invocable: true
tools: Bash, Write
---

## 目标

把全部本地变更自动形成一个 Conventional Commit 并推送到当前分支的 upstream。除发现敏感内容、凭证或合并冲突外，不停止等待用户。

## 执行流程

命令中的 `<skill-dir>` 指本 Skill 所在目录。

### 1. Preflight：固定提交和推送目标

执行：

```bash
bash "<skill-dir>/scripts/preflight.sh"
```

脚本只读 Git 数据，不提交或推送。记录输出的 `CURRENT_BRANCH`、`PUSH_REMOTE`、`PUSH_BRANCH`、`HAS_UPSTREAM`、`UPSTREAM_REF`、工作区状态和 `PENDING_COMMITS`。

如果工作区干净且已有 upstream：

- `PENDING_COMMITS` 为空：报告“无变更”并停止；
- `PENDING_COMMITS` 非空：跳过步骤 2 和 3，直接进入步骤 4。

如果工作区干净且没有 upstream，不创建空提交。

**完成条件**：当前是具名分支；已固定唯一的推送目标；已记录工作区和 upstream 状态。

### 2. 暂存全部变更并做安全检查

执行：

```bash
git status --short
git add -A
bash "<skill-dir>/scripts/inspect-staged.sh"
```

脚本扫描阻止路径并输出 `STAGED_NAME_STATUS` 和 `STAGED_DIFF` 区段。发现阻止路径时停止，由用户决定处理方式。读取完整 `STAGED_DIFF`，发现 API Key、密码、Token、私钥或其他凭证时，列出文件和位置并停止，由用户决定处理方式。

**完成条件**：暂存区包含全部本地变更，不含阻止路径；staged diff 中未发现凭证。

### 3. 自动创建提交

基于 staged diff 生成 Conventional Commit：

- 格式：`<type>(<scope>): <subject>`；
- `type` 使用 `feat`、`fix`、`refactor`、`docs`、`style`、`test` 或 `chore`；
- 第一行 subject 不超过 50 个字符；
- 默认使用中文，除非用户要求英文。

用 Write 工具把生成的实际第一行写入 `/tmp/git-commit-msg.txt`（写入前校验非空且不超过 50 个字符），然后执行：

```bash
git commit -F /tmp/git-commit-msg.txt
rm /tmp/git-commit-msg.txt
```

文件方式让提交信息中的引号和特殊字符不经过 shell 转义，且兼容 bash、zsh 和 fish。

提交失败或 Hook 修改工作区/暂存区时，停止自动重试，重新报告状态并等待用户处理。

**完成条件**：`git commit` 成功；提交后的状态已重新检查；没有把 Hook 新产生的修改误认为已提交内容。

### 4. 推送

提交完成后，在新的 Bash 调用中执行：

```bash
bash "<skill-dir>/scripts/resolve-push-target.sh"
```

脚本重新解析推送目标并刷新远程状态（有 upstream 时先 fetch；远程 URL 中的认证信息已遮蔽）。记录输出的 `CURRENT_BRANCH`、`PUSH_REMOTE`、`PUSH_BRANCH`、`PUSH_REMOTE_URL`、`PUSH_REFSPEC`、`HAS_UPSTREAM`、`IS_PROTECTED_BRANCH`、`REMOTE_AHEAD`、待推送提交和工作区状态。

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

**完成条件**：报告中包含上述全部五项。
