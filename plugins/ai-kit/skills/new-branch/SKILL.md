---
name: new-branch
description: 交互式创建新的开发分支，自动将中文特性描述转换为英文分支名
disable-model-invocation: true
tools: Bash
---

## 执行流程

### 1. 获取用户输入
提示用户输入新特性的名称或描述，例如：
- "用户认证系统"
- "优化数据库查询性能"
- "修复登录页面样式问题"

### 2. 转换为英文描述
将中文翻译为描述性的英文短语：
- kebab-case 格式（单词用 `-` 连接），所有字母小写
- 包含动词（如 optimize, fix, add）和核心对象，清晰表达变更意图
- 控制在 50 个字符以内，优先保证清晰度，不过度简化

转换示例：
- "用户认证系统" → `add-user-authentication-system`
- "优化数据库查询性能" → `optimize-database-query-performance`
- "修复登录页面样式问题" → `fix-login-page-style-issues`
- "优化UT初始化，将验证环节从推理环节分离出来" → `optimize-ut-initialization-separate-verification-from-inference`

### 3. 切换并更新主分支
```bash
# 尝试切换到 main 或 master 分支
git checkout main 2>/dev/null || git checkout master 2>/dev/null

# 确认当前已在主分支上
git branch --show-current

# 更新当前主分支
git pull --ff-only origin HEAD
```

### 4. 检查分支是否存在
```bash
git rev-parse --verify dev/<description>
```

### 5. 创建新分支
```bash
git checkout -b dev/<description>
```

### 6. 确认操作并停止
报告以下信息：
- 新分支名称
- 源分支（main 或 master）
- 切换状态

输出确认后等待用户的下一步指令。在用户发出新指令前不执行任何额外操作。

## 错误处理

- 如果分支已存在，提示用户选择是否覆盖或使用不同的名称
- 如果当前 Git 状态不清洁（有未提交的更改），提示用户先提交或暂存变更
- 如果 main/master 分支不存在，提示错误
- 如果更新主分支失败（如存在冲突或远端不可达），提示用户先处理后再创建分支
