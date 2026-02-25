# AGENTS.md

This file provides guidance to AI agents (Warp, CodeBuddy, etc.) when working with code in this repository.

## Project Overview

`ai-flow-kit` 是一个 **CodeBuddy 插件市场**，提供一系列可复用的 AI 工作流插件，供团队通过 CodeBuddy 的插件系统安装和使用。

## 仓库结构

```
ai-flow-kit/
├── .codebuddy-plugin/
│   └── marketplace.json       # 市场清单（必需）
├── plugins/                   # 所有插件目录
│   └── <plugin-name>/
│       ├── .codebuddy-plugin/
│       │   └── plugin.json    # 插件清单
│       ├── commands/          # 斜杠命令（可选）
│       ├── skills/            # AI 技能（可选）
│       └── hooks/             # 事件钩子（可选）
└── README.md
```

## 如何引用此插件市场

在项目的 `.codebuddy/settings.json` 中添加以下配置：

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
    "my-plugin@ai-flow-kit": true
  }
}
```

## 开发新插件

### 1. 在 `plugins/` 下创建插件目录

```bash
mkdir -p plugins/<plugin-name>/.codebuddy-plugin
```

### 2. 创建 `plugin.json` 清单

参考 `plugins/example-plugin/.codebuddy-plugin/plugin.json` 的格式。

### 3. 更新市场清单

在 `.codebuddy-plugin/marketplace.json` 的 `plugins` 数组中添加新插件条目：

```json
{
  "name": "<plugin-name>",
  "source": "plugins/<plugin-name>",
  "description": "插件描述"
}
```

### 4. 验证插件

```bash
codebuddy plugin validate plugins/<plugin-name>
codebuddy plugin validate .  # 验证整个市场清单
```

## 插件组件说明

- **Skills**：AI 自动识别并调用的专业能力，定义在 `skills/<name>/SKILL.md`
- **Commands**：用户手动触发的斜杠命令（`/<plugin>:<command>`），定义在 `commands/<name>.md`
- **Hooks**：特定事件触发时自动执行的操作，定义在 `hooks/hooks.json`
