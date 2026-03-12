---
name: create-tapd-story
description: 在 TAPD 中创建需求单（Story）。当用户需要提 TAPD 需求、用户故事或功能单时使用。自动收集标题、描述等信息，调用 TAPD REST API 完成建单，并输出链接。
---

# 创建 TAPD 需求单

从用户输入或当前上下文推断需求信息，然后调用脚本建单。

## 必填参数

- **name**：需求标题
- **description_file**：详细描述文件路径（UTF-8，支持 Markdown）

## 调用示例

使用 `{baseDirectory}` 占位符来引用脚本。

### 1. 调用脚本建单

```bash
uv run {baseDirectory}/scripts/create_story.py --name "<需求标题>" --description-file "<描述文件路径>"
```

### 2. 在本地项目备份需求描述

在调用完脚本并获取输出中的 **TAPD ID**（例如 `TAPD ID: #1069995517132461036`）后，你**必须**在当前项目的 `ai-dev/tapd/年/月` 目录下创建一个 Markdown 文件备份需求。

- **目录格式**：`ai-dev/tapd/YYYY/MM/` (例如 `ai-dev/tapd/2026/03/`)
- **文件名**：`story_<TAPD_ID>.md` (例如 `story_1069995517132461036.md`)
- **内容**：完整的需求描述，必须采用 **Markdown 格式**，并进行适当的**格式化排版**（如使用标题、列表、加粗等），以确保易于阅读。

这有助于在本地保留需求记录，并与 TAPD 单号建立关联。
