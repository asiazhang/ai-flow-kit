---
name: new-branch
description: 根据特性描述生成分支名，同步 main/master 后创建开发分支；会切换当前分支、自动暂存并恢复未提交修改
disable-model-invocation: true
user-invocable: true
tools: Bash, AskUserQuestion
---

## 目标

从已同步的 `main`/`master` 创建新的 `dev/<description>` 分支。全程直接执行，无需用户确认；工作区有未提交修改时自动暂存并在新分支上恢复。

## 执行流程

### 1. Preflight：确认仓库可切换

保持目标 Git 仓库为当前工作目录，`<skill-dir>` 为当前已加载 Skill 的目录，执行：

```bash
bash "<skill-dir>/scripts/preflight.sh"
```

工作区可以为空，也可以包含未提交修改；存在进行中的 Git 操作或 `origin` 不可用时脚本会停止。

**完成条件**：脚本输出 `WORKING_TREE_CLEAN` 标记，没有进行中的 Git 操作，`origin` 可用。

### 2. Name：生成名称和基础分支

获取特性描述，优先使用 Skill 调用参数（如 `/new-branch 支持用户导出数据`）；参数为空时用 AskUserQuestion 向用户询问一次非空描述。

由特性描述生成英文 `description`：小写 kebab-case，包含动作和核心对象，不超过 50 个字符；完整分支名 `dev/$description` 不超过 63 个字符。

执行：

```bash
bash "<skill-dir>/scripts/resolve-base.sh"
```

按脚本输出的 `BASE_BRANCH` 和 `BASE_IS_LOCAL` 确定基础分支。

**完成条件**：得到 `branch_name=dev/$description` 和 `base_branch`。

### 3. Action：同步基础分支并创建

传入实际生成的值执行：

```bash
bash "<skill-dir>/scripts/create-branch.sh" \
  --description '<实际生成的 description>' \
  --branch '<实际生成的 dev/branch-name>' \
  --base '<实际选定的 main 或 master>'
```

脚本会校验参数、刷新基础分支并 fast-forward、创建并切换新分支；已跟踪文件的未提交修改会被自动暂存并在新分支上恢复，未跟踪文件随工作区保留。脚本失败时会尝试恢复暂存后停止；恢复冲突时保留 stash 条目，此时直接向用户报告 stash 状态，不要自行执行恢复操作。

**完成条件**：基础分支已 fast-forward 到 `origin/$base_branch`，新分支 `branch_name` 已创建并切换。

### 4. Verify：确认分支状态

`create-branch.sh` 输出 `CURRENT_BRANCH`、`WORKING_TREE_CLEAN`、`STASH_USED` 和 `STASH_RESTORED`，逐项核对：

- `CURRENT_BRANCH` 是 `branch_name`；
- 基础分支同步成功；
- `STASH_USED=true` 时确认 `STASH_RESTORED=true`；此时工作区包含恢复的修改，`WORKING_TREE_CLEAN=false` 是预期状态。

**完成条件**：以上各项全部符合。

### 5. Report：汇报

报告新分支名称、基础分支及其来源（本地或 `origin`）、当前分支状态、未提交修改是否被自动暂存并恢复到新分支。
