---
name: new-branch
description: 根据用户确认的特性描述生成分支名，同步 main/master 后创建开发分支；会切换当前分支并修改本地分支引用
disable-model-invocation: true
user-invocable: true
tools: Bash, AskUserQuestion
---

## 目标

在干净仓库中，从已同步的 `main` 或 `master` 创建一个新的 `dev/<description>` 分支。生成名称和基础分支后先请求确认，再执行切换和创建。

## 执行流程

### 1. Preflight：确认仓库可切换

保持目标 Git 仓库为当前工作目录，使用当前已加载 Skill 的目录作为 `<skill-dir>`，执行：

```bash
bash "<skill-dir>/scripts/preflight.sh"
```

脚本确认仓库根目录、工作区、进行中的 Git 操作和 `origin`。工作区必须为空；存在 merge、cherry-pick、revert、bisect 或 rebase 状态时停止。

**完成条件**：已进入仓库根目录；工作区为空；没有进行中的 Git 操作；`origin` 可用。

### 2. Name gate：生成并确认名称和基础分支

向用户获取非空特性描述，生成英文 `description`：

- 使用小写 kebab-case；
- 包含动作和核心对象；
- `description` 不超过 50 个字符；
- 完整分支名为 `dev/$description`，不超过 63 个字符。

使用实际生成的值验证：

```bash
branch_name="dev/$description"

[ -n "$description" ] || {
  echo "特性描述为空，已停止。" >&2
  exit 1
}

[ "${#branch_name}" -le 63 ] || {
  echo "完整分支名超过 63 个字符，已停止。" >&2
  exit 1
}

git check-ref-format --branch "$branch_name" >/dev/null || {
  echo "生成的分支名不符合 Git ref 规则，已停止。" >&2
  exit 1
}
```

执行：

```bash
bash "<skill-dir>/scripts/resolve-base.sh"
```

按脚本输出的 `BASE_BRANCH` 和 `BASE_IS_LOCAL` 确定基础分支。优先级为当前就在的 `main`/`master`、本地 `main`、本地 `master`、`origin/main`、`origin/master`、远程查询到的 `origin/main`、远程查询到的 `origin/master`。

向用户展示并请求确认：

- 生成的分支名；
- 选定的基础分支；
- 将同步 `origin/<base_branch>`，并可能切换当前分支。

用户拒绝时停止；确认前不修改本地分支状态。

**完成条件**：用户确认了合法的 `branch_name` 和 `base_branch`；确认前没有修改本地分支状态。

### 3. Action：同步基础分支并创建

用户确认后，在新的 Bash 调用中使用用户确认的实际值执行：

```bash
bash "<skill-dir>/scripts/create-branch.sh" \
  --description '已确认的实际 description' \
  --branch '已确认的实际 dev/branch-name' \
  --base '已确认的实际 main 或 master'
```

不得保留中文示例值。脚本会重新检查工作区和 Git 操作状态，确认本地和 `origin` 没有同名分支，刷新已确认的基础分支，用 `git merge --ff-only` 同步后创建并切换新分支。它只接受显式确认后的值，不重新生成名称，也不自动覆盖已有分支。

**完成条件**：基础分支已 fast-forward 到 `origin/$base_branch`，并已创建 `branch_name`。

### 4. Verify：确认分支状态

`create-branch.sh` 会输出 `CURRENT_BRANCH` 和 `WORKING_TREE_CLEAN`。确认当前分支是 `branch_name`，工作区为空，基础分支同步成功。

**完成条件**：当前分支是 `branch_name`，工作区为空，基础分支同步成功。

### 5. Report：汇报

报告：

- 新分支名称；
- 基础分支；
- 基础分支来自本地还是 `origin`；
- 当前分支和工作区状态。

报告完成后停止，等待用户下一步指令。
