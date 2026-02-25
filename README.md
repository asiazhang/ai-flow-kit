# AI Flow Kit

> A curated CodeBuddy plugin marketplace for AI workflow development.

## 简介

`ai-flow-kit` 是一个 [CodeBuddy](https://www.codebuddy.cn) 插件市场，提供一系列专为 AI 工作流设计的插件，帮助团队快速构建和标准化 AI 辅助开发流程。

## 快速开始

在你的项目中添加 `.codebuddy/settings.json`：

```json
{
  "extraKnownMarketplaces": {
    "ai-flow-kit": {
      "source": {
        "source": "github",
        "repo": "zhangheng/ai-flow-kit"
      }
    }
  },
  "enabledPlugins": {
    "ai-kit@ai-flow-kit": true
  }
}
```

## 可用插件

| 插件名 | 描述 |
|--------|------|
| `ai-kit` | AI 工作流辅助工具集，提供分支变更摘要等实用命令 |

## 贡献

参考 [AGENTS.md](./AGENTS.md) 了解如何开发和添加新插件。
自定义AI工作流
