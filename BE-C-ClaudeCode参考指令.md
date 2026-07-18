# 团队成员（BE-C） Claude Code 参考指令手册

> **用法**：每人找到自己角色的章节，按时间节点复制粘贴指令给 Claude Code。每个指令独立可用，完成后在群内同步。

---

## 使用说明

每个指令卡片包含 4 个信息：
- **复制给 Claude**：直接复制粘贴给 Claude Code
- **实现什么功能**：这个指令会产生什么产出
- **完成后如何交接**：完成后你要做什么、发给谁
- **何时执行下一阶段**：下一条指令的触发条件

---

---
# BE-C 角色指令（2 条）

---

## BE-C 指令 #1 — 构建 RAG 知识库

**🕐 执行时间**：09:15（启动会后立即执行）

### 复制给 Claude

```
帮我构建在线教育平台的 RAG 知识库，为演示做准备。

项目 RAG 技术栈（CLAUDE.md 决策 4）：
- ChromaDB 0.5.3（Docker 容器 chromadb/chroma:0.5.3，端口 8001）
- LangChain 0.2.x
- 知识库构建 API：POST /api/v1/courses/{course_id}/knowledge-base/build

我需要你：

1. 启动 ChromaDB：
   docker compose up -d chromadb
   验证：curl http://localhost:8001/api/v1/heartbeat

2. 准备演示用的 PDF 文档（3-5 个课程相关资料）：
   - 如果没有现成的 PDF，帮我创建几个 markdown 文件作为替代
   - 内容覆盖：机器学习基础、Python 编程、数据结构等课程主题
   - 放在 data/ 目录下

3. 调用知识库构建 API 上传文档：
   - 查看 app/api/v1/qa.py 中的知识库构建端点
   - 查看 app/services/rag_service.py 中的构建逻辑
   - 先对 course_id=1 构建知识库
   - 确认向量数据已存入 ChromaDB

4. 验证检索效果：
   POST /api/v1/qa/ask { "course_id": 1, "question": "什么是机器学习？" }
   确认返回了有意义的回答

如果遇到 API 404 或导入错误，帮我修复一直到知识库构建成功为止。
```

### 实现什么功能

- 为演示准备 RAG 的向量化数据
- 确保 ChromaDB 正常运行，知识库构建 API 可用
- 演示时 PM 可以用 Postman 调用 `/api/v1/qa/ask` 展示 AI 流式问答

### 完成后如何交接

1. 在群里发：
   **"知识库构建完成，3 个 PDF 文档已入库。SSE 问答已可用：POST /api/v1/qa/ask"**
2. 然后继续执行 BE-C 指令 #2
3. 将构建成功的问答示例（问题 + 回答前几行）截图发到群里，让大家有直观认知

### 何时执行下一阶段

知识库构建成功 + SSE 问答验证通过后，立即执行 BE-C 指令 #2

---

## BE-C 指令 #2 — 准备 RAG 演示材料

**🕐 执行时间**：11:00（知识库构建完成后）

### 复制给 Claude

```
帮我准备 RAG 问答功能的演示材料。

需要产出 3 个文件：

1. scripts/test_sse.py — SSE 流式问答测试脚本
   - 用 Python requests 库调用 POST /api/v1/qa/ask
   - 需要带 cookie 认证（access_token + csrf_token）
   - 流式读取 response，逐行打印 SSE 事件
   - 使用方法写在脚本注释顶部

2. docs/postman/RAG-Demo.postman_collection.json — Postman 集合
   包含 4 个接口：
   - POST /api/v1/courses/{id}/knowledge-base/build（知识库构建）
   - POST /api/v1/qa/ask（SSE 流式问答，标注"响应为 SSE 流"）
   - GET /api/v1/qa/history（问答历史）
   - POST /api/v1/assistant/similar-questions（相似题推荐）
   每个接口要包含 example 请求体和说明

3. 演示话术草稿（文本，不需要文件）：
   - "现在演示 RAG 问答功能：基于刚才上传的课程资料..."
   - "这是 SSE 流式返回，可以看到答案逐字生成..."
   - "右侧是引用来源，标注答案来自课程材料的哪一部分..."

认证相关：
- 登录接口 POST /api/v1/auth/login 获取 cookie
- 所有接口需要 access_token cookie + X-CSRF-Token header
- Postman 集合中标注如何配置环境变量（base_url, csrf_token）
```

### 实现什么功能

- PM 可以在终端运行 `python scripts/test_sse.py` 演示流式问答
- PM 可以在 Postman 中导入集合，点击即可演示 4 个 RAG 接口
- 演示话术让 PM 在最终演示时有条理地介绍 RAG 功能

### 完成后如何交接

1. 提交到集成分支：
```bash
git checkout integration-day3
git pull origin integration-day3
git add scripts/test_sse.py docs/postman/
git commit -m "feat(rag): 添加 SSE 测试脚本与 RAG 演示 Postman 集合"
git push origin integration-day3
```
2. 在群里发：
```
@所有人 M4 已合并！RAG 演示材料就绪
@PM Postman 集合在 docs/postman/，测试脚本在 scripts/test_sse.py
```
3. 之后你的角色转为"协助 FE 联调"
4. 与 PM 单独同步，演练一遍 RAG 演示流程

### 何时执行下一阶段

无独立指令。BE-C 指令 #2 完成后，你转为支持角色：
- 协助 FE 调试前端样式和页面交互
- 在 16:00 的全链路测试中，负责 RAG 部分的功能验证
- 17:00 演示时，在后台准备好 Postman 和终端，随时进行 RAG 演示

---

# 附录 A：群内通知模板

## 启动通知（09:00 PM 发送）

```
@所有人 今日集成开发启动！

集成分支：integration-day3
文档：集成分支开发指南.md + 团队成员ClaudeCode参考指令.md

请按开发指南中的顺序提交：
M1 (10:30) DBA → M2 (11:00) BE-A → M3 (12:00) BE-B → M4 (13:30) BE-C → M5 (16:00) FE

每个人打开"团队成员ClaudeCode参考指令.md"找到自己角色的指令，
直接复制粘贴给 Claude Code 即可开始工作。

提交前务必先：git pull origin integration-day3
```

## 合并通知（每次合并后发送）

```
@所有人 [Mx] 已合并！

合并内容：xxx

请立即执行：
git pull origin integration-day3

被解锁的下一步：
- FE 可以开始 xxx
- PM 请验收 xxx
```

## 站会通知（每 2 小时）

```
===== 站会 (10:30) =====
DBA:   [完成/进行中/阻塞]
BE-A:  [完成/进行中/阻塞]
BE-B:  [完成/进行中/阻塞]
BE-C:  [完成/进行中/阻塞]
FE:    [完成/进行中/阻塞]
PM:    [验收结果/风险提示]
=====================
```

---

# 附录 B：每个角色执行顺序总览

```
DBA：  指令#1 (09:15) → 提交M1 (10:30) → 指令#2 → 转为技术支持
BE-A： 指令#1 (09:15) → 提交M2 (11:00) → 指令#2 → 转为 FE 联调
BE-B： 指令#1 (09:15) → 提交M3 (12:00) → 指令#2 → 转为 FE 联调
BE-C： 指令#1 (09:15) → 指令#2 (11:00) → 提交M4 (13:30) → 转为 FE 联调
FE：   指令#1 (09:15) → 指令#2 (10:30) → 指令#3 (11:00) → 午休 → 指令#4 (13:30) → 指令#5 (14:30) → 提交M5 (16:00)
PM：   指令#1 (09:15) → 指令#2 (10:30) → 指令#3 (11:00) → 午休 → 指令#4 (16:00) → 演示 (17:00)
```

---

**立即开始！每人打开自己的角色章节，复制第一条指令给 Claude Code。**
