---
name: refine-requirements
description: 读取需求文档并扫描代码，补充完善该文档并增加实施步骤
allowed-tools: Read, Write, Edit, Glob, Grep, Task
---

请使用 `refine-requirements` 子代理来完成需求完善任务。该代理将读取用户指定的需求文档（Markdown 格式），扫描当前代码库以了解背景，并直接在原文档中补充更详细的需求描述和具体的实施步骤。
