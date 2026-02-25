---
name: create-tapd-story
description: 在 TAPD 中创建需求单（Story）。当用户需要提 TAPD 需求、用户故事或功能单时使用。自动收集标题、描述等信息，调用 TAPD REST API 完成建单，并输出链接。
---

# 创建 TAPD 需求单

从用户输入或当前上下文推断需求信息，然后调用脚本建单。

## 必填参数

- **name**：需求标题
- **description**：详细描述，支持 Markdown

## 调用示例

```bash
uv run scripts/create_story.py --name "<需求标题>" --description "<描述>"
```

配置从项目根目录 `.dev.env` 读取：
- `TAPD_API_TOKEN` - API 令牌
- `TAPD_DEFAULT_OWNER` - 默认处理人
- `TAPD_ITERATION_ID` - 迭代 ID
- `TAPD_CATEGORY_ID` - 任务分类 ID
