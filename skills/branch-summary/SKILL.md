---
name: branch-summary
description: 分析当前分支相对 main/master 的已提交变更，并用中文总结修改意图；会同步 origin，不包含未提交修改
disable-model-invocation: true
user-invocable: true
tools: Bash
---

## 目标

只分析当前 `HEAD` 相对主干的**已提交变更**。工作区修改只用于提示状态，一律不作为摘要证据。

## 执行流程

### 1. Evidence：收集证据

在目标仓库中，使用当前已加载 Skill 的目录作为 `<skill-dir>`，执行：

```bash
bash "<skill-dir>/scripts/collect-evidence.sh"
```

脚本定位仓库根目录、同步 `origin`、选择主干基准，并输出带区段标记的提交列表（不含同步主干的合并提交）、diff 统计和完整 diff。分支已合入主干时，脚本自动回退到合并前的主干作基准并标记 `BRANCH_MERGED=true`。所有数据从脚本输出读取，比较基准以其中的 `BASE_REF` 为准。

脚本失败时报告错误并停止。脚本对仓库只读，但 `git fetch --prune origin` 会更新本地远程跟踪引用。

**完成条件**：已成功读取 `COMMITS`、`DIFF_STAT` 和 `DIFF` 区段；无已提交文件变更时，已读取 `SUMMARY_STATUS`；已记录工作区状态。

### 2. Reason：提炼修改意图

只根据提交信息和 diff 提炼意图。每个“变更原因”都必须能从提交或 diff 找到依据；无法确认的业务背景标为“推测”。

**完成条件**：每个摘要判断都能回溯到提交信息或 diff。

### 3. Report：按固定格式输出

严格输出以下三个部分，顺序固定：

```text
**核心目标**：一句话概括最高层级目标；未提交修改：无/存在，但未纳入本摘要。

**变更原因与改进**：
- **关键词**：说明有证据支持的痛点和改进。
- **关键词**：补充有证据支持的影响。

**关键技术点**：一句话概括涉及的模块、架构调整或技术手段。
```

没有已提交文件变更时，仍输出三部分；在“核心目标”中明确“相对 `<BASE_REF>` 没有已提交文件变更”。`BRANCH_MERGED=true` 时，在“核心目标”中注明“分支已合入主干（`<MERGE_COMMIT>`）”。

**完成条件**：输出与上述模板及空变更规则逐项一致。
