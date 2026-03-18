---
name: create-tapd-story
description: 在 TAPD 中创建需求单（Story）。调用此技能以执行底层的建单脚本。
---

# 创建 TAPD 需求单 (Skill)

此技能负责调用底层的 Python 脚本来完成 TAPD 需求单的创建。更高级的需求分析、标题生成和本地备份逻辑请参考 `create-tapd-story` 子代理。

## 必填参数

- **name**：需求标题
- **description_file**：详细描述文件路径（UTF-8，支持 Markdown）

## 调用示例

使用 `{baseDirectory}` 占位符来引用脚本。

```bash
uv run {baseDirectory}/scripts/create_story.py --name "<name>" --description-file "<description_file>"
```
