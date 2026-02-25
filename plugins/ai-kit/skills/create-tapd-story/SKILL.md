---
name: create-tapd-story
description: 在 TAPD 中创建需求单（Story）。当用户需要提 TAPD 需求、用户故事或功能单时使用。自动收集标题、描述、优先级、处理人等信息，调用 TAPD REST API 完成建单，并输出链接。
---

# 创建 TAPD 需求单

从用户输入或当前上下文推断需求信息，然后调用脚本建单。

## 必填参数

- **name**：需求标题

## 可选参数

- **description**：详细描述，支持 HTML
- **priority**：`High` / `Middle`（默认） / `Low` / `Nice To Have`
- **status**：初始状态（如：研发中）
- **label**：标签，多个用 `|` 分隔
- **cc**：抄送人用户名，多人用 `;` 分隔
- **version**：版本
- **parent-id**：父需求 ID

## 调用示例

```bash
# 最简（owner/迭代/分类等从 .env 自动读取）
python3 scripts/create_story.py --name "<需求标题>" --description "<描述>"

# 指定优先级和标签
python3 scripts/create_story.py \
  --name "<需求标题>" \
  --description "<描述>" \
  --priority "High" \
  --label "标签A|标签B"
```

配置从项目根目录 `.env` 读取，详细字段说明见 [references/tapd-api.md](references/tapd-api.md)。
