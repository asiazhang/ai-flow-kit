---
name: clean-branches
description: 检查本地 Git 分支，清理远程已删除的失效分支
disable-model-invocation: true
user-invocable: true
tools: Bash
---

## 执行流程

### 1. 同步远程状态并检索失效分支
```bash
git fetch -p
```
如果 `git fetch -p` 失败（网络或权限问题），提示用户检查环境并终止后续步骤。

```bash
git branch -vv | grep ': gone]' | awk '{print $1}' | sed 's/^\*//'
```

### 2. 判断结果
- 输出为空 → 告知"本地仓库没有需要清理的失效分支"，跳到步骤 6。
- 有分支 → 解析分支名，进入步骤 3。如果当前分支也在列表中，提醒用户先切换到其他分支再重试。

### 3. 确认删除
列出所有失效分支名，询问："以下分支在远程已删除，将被强制清理（`git branch -D`），是否确认？"

### 4. 执行删除
确认后，逐个执行：
```bash
git branch -D <branch-name>
```

### 5. 报告结果
列出成功删除和删除失败的分支。

### 6. 列出当前分支
```bash
git branch
```

## 输出示例
```
正在检查远程分支状态...

发现本地有 2 个远程已删除的分支：
- feature/old-task-1
- fix/temp-bug

已清理 2 个分支。

当前本地分支：
* main
  dev/new-feature
```
