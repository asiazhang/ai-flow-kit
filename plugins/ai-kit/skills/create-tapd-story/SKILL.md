---
name: create-tapd-story
description: 在 TAPD 中创建需求单。
disable-model-invocation: true
user-invocable: true
tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

## 执行流程

1. **推断需求**：基于对话历史、代码现状，自主提炼背景、目标和技术要点。
   - 只在核心需求完全无法推断时，才用 `AskUserQuestion` 询问最关键的功能描述。
   - 其余细节基于现有信息合理推演，不追问。

2. **生成标题与描述**：输出一份包含背景、目标、功能要求、验收标准的 Markdown 描述，并从中提炼一句简洁的需求标题。
   - 完成标准：标题和描述都已就绪，可以写入文件。

3. **调用建单脚本**：

   ```bash
   uv run {baseDirectory}/scripts/create_story.py --name "<标题>" --description-file "<描述临时文件>"
   ```

   - 完成标准：脚本输出 `TAPD ID: #<ID>`。

4. **本地备份**：在 `ai-dev/tapd/YYYY/MM/` 下创建 `story_<TAPD_ID>.md`，写入完整描述。
   - 目录日期取当前日期。
   - 完成后向用户展示 TAPD 链接。
