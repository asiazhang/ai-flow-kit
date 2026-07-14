---
name: branch-summary
description: 分析当前 Git 分支相对于主干分支（main/master）的所有变更，输出一段重点阐述"为什么要做这些修改"的简要中文描述
disable-model-invocation: true
user-invocable: true
tools: Bash
---

## 执行流程

1. 获取当前分支名：
   ```bash
   git branch --show-current
   ```

2. 确定主干分支（尝试 `main`，不存在则用 `master`）：
   ```bash
   git branch --list main master | sed 's/^[* ]*//' | head -1
   ```

3. 同步本地主干分支：
   ```bash
   git --no-pager fetch origin <base>:<base>
   ```

4. 获取提交历史：
   ```bash
   git --no-pager log <base>..HEAD --oneline
   ```

5. 获取变更 diff：
   ```bash
   git --no-pager diff <base>...HEAD
   ```

6. 基于提交信息和 diff 提炼变更意图，按以下结构输出三段摘要。

## 输出格式

**严格按三段输出，顺序固定：**

1. **核心目标**：一句话概括本次变更的最高层级目标。
2. **变更原因与改进**：以列表和粗体关键词阐述解决了什么痛点、带来什么改进。
3. **关键技术点**：简要说明涉及的主要模块、架构调整或技术手段。

阐述遵循**意图优先**：解释"为什么要改"重于描述"改了什么"。每段使用列表和粗体关键词。

### 输出示例

**核心目标**：优化单元测试初始化流程，实现验证逻辑与推理流程的解耦。

**变更原因与改进**：
- **解耦验证与推理**：原有流程中验证环节深度耦合导致推理上下文污染和硬超时风险，拆分为"推理"与"原子化验证修复"两个独立阶段。
- **增强稳定性与并发**：每个组件在独立 AI 会话中验证，具备自愈能力。
- **规范化文档与代码**：统一规范文件命名，移除 `dotimport` 并补全文档注释。

**关键技术点**：架构分层重构、文档规范统一、代码风格优化。
