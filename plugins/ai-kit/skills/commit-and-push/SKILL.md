---
name: commit-and-push
description: 暂存更改、生成提交信息并推送到远程仓库
disable-model-invocation: true
user-invocable: true
tools: Bash, Write, AskUserQuestion
---

## 1. 检查状态

```sh
git rev-parse --is-inside-work-tree
git status --short
```

完成条件：`git status --short` 输出空 → 检查 `git log origin/HEAD..HEAD --oneline` 是否有未推送提交；有则跳过暂存和提交，直接执行推送（Step 4）。无任何变更且无未推送提交 → 告知用户"无变更"并停止。非空 → 继续。

## 2. 暂存文件

跳过以下文件模式：`.env`、`*.log`、`node_modules/`、`dist/`、`.DS_Store`、疑似临时或备份文件。

扫描变更内容：发现明文凭证（API Key、密码、Token 等）时，暂停并向用户确认是否跳过。

逐一暂存其余文件：`git add <path>`。若工作区存在大量互不相关的变更，先向用户确认需要提交哪些文件，再逐一暂存。

完成条件：`git --no-pager diff --cached --name-only` 列出所有目标文件，且不含任何跳过模式。

## 3. 提交

执行 `git --no-pager diff --cached`，基于变更生成 Conventional Commits 格式的提交信息：

- 格式：`<type>(<scope>): <subject>`
- 类型：feat、fix、refactor、docs、style、test、chore
- Subject 不超过 50 字符，默认中文（除非用户要求英文）

使用 Write 工具将提交信息写入 `/tmp/git-commit-msg.txt`，然后执行：

```sh
git commit -F /tmp/git-commit-msg.txt
rm /tmp/git-commit-msg.txt
```

此路径兼容 bash、zsh 和 fish。

若 pre-commit hook 修改了暂存文件：重新暂存并重新提交。

完成条件：`git commit` 执行成功，暂存区无残留变更（`git diff --cached` 空）。提交信息符合 Conventional Commits 格式，subject ≤50 字符。

## 4. 推送

```sh
git branch --show-current
git push -u origin HEAD
```

若推送因远程更新被拒绝（non-fast-forward）：

```sh
git pull --rebase origin <current_branch>
git push origin HEAD
```

若 rebase 出现冲突：停止操作，报告冲突文件路径，让用户手动解决。

完成条件：`git status` 显示分支已与 origin 同步。输出摘要：推送的提交（哈希+消息）、推送分支。若 Step 2-3 已执行：附加已提交文件、已跳过文件。
