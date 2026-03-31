# AGENTS.md

This file provides guidance to AI agents (Claude Code, CodeBuddy, etc.) when working with code in this repository.

## Project Overview

`ai-flow-kit` 是一个**双平台插件市场**，同时支持 Claude Code 和 CodeBuddy，提供一系列可复用的 AI 工作流插件，供团队安装和使用。

## 仓库结构

```
ai-flow-kit/
├── .claude-plugin/
│   └── marketplace.json       # Claude Code 市场清单
├── .codebuddy-plugin/
│   └── marketplace.json       # CodeBuddy 市场清单
├── plugins/                   # 所有插件目录
│   └── <plugin-name>/
│       ├── .claude-plugin/
│       │   └── plugin.json    # Claude Code 插件清单
│       ├── .codebuddy-plugin/
│       │   └── plugin.json    # CodeBuddy 插件清单
│       ├── commands/          # 斜杠命令（可选）
│       ├── agents/            # AI 子代理（可选）
│       ├── skills/            # AI 技能（可选）
│       └── hooks/             # 事件钩子（可选）
└── README.md
```

## 如何引用此插件市场

### Claude Code

在项目的 `.claude/settings.json` 中添加以下配置：

```json
{
  "extraKnownMarketplaces": {
    "ai-flow-kit": {
      "source": {
        "source": "git",
        "repo": "git@git.woa.com:pinhenzhang/ai-kit.git"
      }
    }
  },
  "enabledPlugins": {
    "ai-kit@ai-flow-kit": true
  }
}
```

### CodeBuddy

在项目的 `.codebuddy/settings.json` 中添加以下配置：

```json
{
  "extraKnownMarketplaces": {
    "ai-flow-kit": {
      "source": {
        "source": "git",
        "repo": "git@git.woa.com:pinhenzhang/ai-kit.git"
      }
    }
  },
  "enabledPlugins": {
    "ai-kit@ai-flow-kit": true
  }
}
```

## 开发新插件

### 1. 在 `plugins/` 下创建插件目录

```bash
mkdir -p plugins/<plugin-name>/.claude-plugin
mkdir -p plugins/<plugin-name>/.codebuddy-plugin
```

### 2. 创建插件清单

**Claude Code**（`plugins/<plugin-name>/.claude-plugin/plugin.json`）：
```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "插件描述",
  "commands": ["commands/<cmd>"],
  "agents": "./agents/",
  "skills": ["skills/<skill>"],
  "hooks": ""
}
```

**CodeBuddy**（`plugins/<plugin-name>/.codebuddy-plugin/plugin.json`）同上格式。

### 3. 更新市场清单

在 `.claude-plugin/marketplace.json` **和** `.codebuddy-plugin/marketplace.json` 的 `plugins` 数组中各添加一条：

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "source": "plugins/<plugin-name>",
  "description": "插件描述"
}
```

### 4. 编写 agents

agent 文件存放在 `plugins/<plugin-name>/agents/<name>.md`，格式如下：

```markdown
---
name: agent-name
description: 该代理的用途描述（Claude Code 依据此字段自动判断调用时机）
tools: Bash, Read, Write, Edit, Glob, Grep
---

系统提示词内容...
```

**注意：**
- **不要设置 `model` 字段**，省略后各平台会使用自身默认模型，同时兼容 Claude Code 和 CodeBuddy
- Claude Code **不支持** `color` 字段，请勿添加
- `tools` 值为逗号分隔字符串，不使用 YAML 数组（`[...]`）格式

### 5. 验证插件

```bash
# Claude Code
claude /plugin validate plugins/<plugin-name>

# CodeBuddy
codebuddy plugin validate plugins/<plugin-name>
codebuddy plugin validate .  # 验证整个市场清单
```

## 插件组件说明

- **Agents**：AI 子代理，定义在 `agents/<name>.md`，可被 commands 或其他代理调用
- **Skills**：AI 自动识别并调用的专业能力，定义在 `skills/<name>/SKILL.md`
- **Commands**：用户手动触发的斜杠命令（`/<plugin>:<command>`），定义在 `commands/<name>.md`
- **Hooks**：特定事件触发时自动执行的操作，定义在 `hooks/hooks.json`
