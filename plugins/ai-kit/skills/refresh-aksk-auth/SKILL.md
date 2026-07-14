---
name: refresh-aksk-auth
description: 刷新 AKSK 认证并生成 set-aksk 临时命令文件，输出可执行文件路径
disable-model-invocation: true
user-invocable: true
tools: Bash
---

## 执行流程

1. 提示用户自行登录
   - 提示用户在 devcontainer 终端执行：`bazel run //:cloudctl -- login`
   - 引导用户按命令输出完成登录（打开链接、复制验证码等）
   - 等待用户明确反馈"已完成登录"

2. 查询并记录身份
   - 执行：`bazel run //:cloudctl -- whoami`
   - 解析输出，记录 user/account/tenant 身份信息
   - 失败：提示确认登录状态，重试 whoami

3. 获取并记录凭证
   - 使用第二步的用户名执行：`bazel run //:cloudctl -- get-aksk -p <用户名称>`
   - 解析输出，记录 SecretId、SecretKey、Token
   - 缺字段：提示重试并停止后续步骤
   - 失败：提示确认用户名，重试 get-aksk

4. 生成临时命令文件
   - 组装命令：`bazel run //:cloudctl -- set-aksk -p <用户名称> --aksk <SecretId:SecretKey[:Token]>`
   - 将完整命令写入 `/tmp/refresh-aksk-<timestamp>.sh`
   - 执行 `chmod 600` 设置文件权限
   - 向用户输出文件路径，提示按需执行
   - 写入失败：提示检查 `/tmp` 权限或改用用户指定目录
   - 终端仅展示脱敏后的密钥值，完整密钥通过文件传递
