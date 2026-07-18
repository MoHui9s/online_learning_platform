# 团队成员 Claude Code 参考指令手册

> **用法**：每人找到自己角色的章节，按时间节点复制粘贴指令给 Claude Code。每个指令独立可用，完成后在群内同步。

---

## 使用说明

每个指令卡片包含 4 个信息：
- **复制给 Claude**：直接复制粘贴给 Claude Code
- **实现什么功能**：这个指令会产生什么产出
- **完成后如何交接**：完成后你要做什么、发给谁
- **何时执行下一阶段**：下一条指令的触发条件

---

# DBA 角色指令（2 条）

---

## DBA 指令 #1 — 添加性能索引

**🕐 执行时间**：09:15（启动会后立即执行）

### 复制给 Claude

```
我在做在线教育平台的数据库优化。先帮我检查当前 MySQL 数据库中所有表的索引情况，然后做以下工作：

1. 连接数据库（配置在 app/core/config.py），列出所有表的现有索引
2. 分析高频查询模式：
   - 用户查我的课程：SELECT * FROM enrollments WHERE user_id = ?
   - 用户查学习记录：SELECT * FROM learning_records WHERE user_id = ? AND courseware_id = ?
   - 用户查考试记录：SELECT * FROM exam_records WHERE user_id = ? AND exam_id = ?
   - 课程列表筛选：SELECT * FROM courses WHERE status = ?
3. 为上述查询添加缺失的复合索引
4. 用 EXPLAIN 验证索引效果
5. 不要修改模型文件，只输出需要添加的 SQL 语句

目录结构：app/models/ 下是 SQLAlchemy 模型，数据库配置在 app/core/config.py 和 app/core/database.py
```

### 实现什么功能

- 为 `enrollments`、`learning_records`、`exam_records` 等高频查询表添加复合索引
- 直接提升 API 响应速度（选课列表、学习进度、考试记录的查询都会更快）

### 完成后如何交接

1. 将 Claude 给出的 SQL 语句保存为 `scripts/add_indexes.sql`
2. 在群里发：**"DBA 索引分析完成，SQL 已保存到 scripts/add_indexes.sql，需要手动执行或写进 Alembic 迁移"**
3. 继续执行 DBA 指令 #2

### 何时执行下一阶段

立即执行 DBA 指令 #2（索引分析和演示数据生成可以并行，但建议先完成索引再写数据脚本）

---

## DBA 指令 #2 — 生成演示数据脚本

**🕐 执行时间**：10:00（索引分析完成后）

### 复制给 Claude

```
帮我写一个演示数据生成脚本 scripts/generate_demo_data.py，用于在线教育平台 MVP 演示。

数据要求：
1. 10 个用户：5 个学生（student1-5，密码都是 123456）+ 5 个老师（teacher1-5）
2. 5 个课程，每个课程属于不同分类，status 为 published
3. 每个课程 3 个章节（树形结构，第1章为根，2-3章为子节点）
4. 每个章节 2 个课件（type 为 video，file_path 填 /static/videos/demo.mp4）
5. 每个学生选 2-3 门课（enrollments 表）
6. 20 个知识点（树形，3 个一级 + 各 3-4 个子级）
7. 30 个题目（单选/多选/判断各 10 个），绑定到知识点
8. 5 个考试（每门课 1 个），每个考试 10 题
9. 模拟学习记录：每个学生已观看 50-80% 的课件进度

技术要求：
- 参考 app/models/ 下的 SQLAlchemy 模型定义字段
- 密码哈希用 app/core/security.py 的 pwd_context.hash("123456")
- 使用 app/core/database.py 的 SessionLocal 获取数据库会话
- 脚本可以重复执行（先清空再插入）

写完后告诉我如何执行这个脚本。
```

### 实现什么功能

- 一键生成完整的演示数据集
- 10 个用户、5 门课程、15 个章节、30 个课件、20 个知识点、30 道题目、5 个考试、模拟进度
- PM 演示时不用手动录入数据，直接运行脚本即可

### 完成后如何交接

1. 执行脚本验证数据：`conda run -n edu_platform python scripts/generate_demo_data.py`
2. 验证数据量：`mysql> SELECT COUNT(*) FROM users;`（应该是 10 条）
3. 提交到集成分支：
```bash
git checkout integration-day3
git pull origin integration-day3
git add scripts/generate_demo_data.py scripts/add_indexes.sql
git commit -m "feat(db): 添加性能索引与演示数据生成脚本"
git push origin integration-day3
```
4. 在群里发：
```
@所有人 M1 已合并！拉取最新代码后执行：
conda run -n edu_platform python scripts/generate_demo_data.py
```
5. 之后你的角色转为"技术支持"，协助 PM 和 FE 排查数据相关问题

### 何时执行下一阶段

无独立指令。M1 后你的工作是：
- 数据验证（确认脚本生成的数据正确）
- 性能监控（数据库连接池、慢查询）
- 16:00 后协助 PM 执行 Docker 部署

---

# BE-A 角色指令（2 条）

---

## BE-A 指令 #1 — 添加学习进度上报 API

**🕐 执行时间**：09:15（启动会后立即执行）

### 复制给 Claude

```
我在在线教育平台的 backend 目录下工作，需要添加一个学习进度上报 API。

背景：
- 项目使用 FastAPI + SQLAlchemy 2.0 + Pydantic v2
- 已有 learning_records 表（模型在 app/models/learning_record.py）和 learning_calendar 表（模型在 app/models/learning_calendar.py）
- API 规范：统一前缀 /api/v1/，统一响应体 { code, data, message }
- 认证：依赖 get_current_user，参考现有路由写法
- 路由挂载：在 app/api/v1/__init__.py 中注册

我需要你：

1. 创建 app/schemas/learning.py，定义 ProgressUpdate schema：
   - courseware_id: int（必填）
   - progress: int（必填，0-100，播放进度百分比）
   - duration: int（必填，本次学习时长秒数）

2. 创建 app/services/learning_service.py，实现 update_progress 方法：
   - 查找或创建 learning_records 记录（按 user_id + courseware_id 去重）
   - 如果已有记录：progress 取最大值，duration 累加，更新 last_learn_at
   - 如果是新记录：创建新记录
   - 同步更新 learning_calendar（按 user_id + learn_date 聚合 duration）

3. 创建 app/api/v1/learning.py：
   - POST /learning/progress 路由
   - 接收 ProgressUpdate body
   - 调用 learning_service.update_progress
   - 返回 success(message="进度已保存")

4. 在 app/api/v1/__init__.py 挂载 learning.router

参考现有代码风格（app/api/v1/enroll.py 的路由写法、app/services/enrollment.py 的服务层写法）。
```

### 实现什么功能

- 前端 VideoPlayer 每 30 秒调用 `POST /api/v1/learning/progress` 上报播放进度
- 后端记录每次学习行为：看了哪个课件、看了多久、进度百分比
- learning_calendar 按天聚合学习时长，供统计页的热力图使用

### 完成后如何交接

1. 本地测试：
```bash
# 启动后端
conda run -n edu_platform uvicorn app.main:app --reload

# Postman 测试
curl -X POST http://localhost:8000/api/v1/learning/progress \
  -H "X-CSRF-Token: xxx" \
  -b "access_token=xxx; csrf_token=xxx" \
  -H "Content-Type: application/json" \
  -d '{"courseware_id":1,"progress":45,"duration":30}'
```
2. 提交到集成分支：
```bash
git checkout integration-day3
git pull origin integration-day3
git add app/schemas/learning.py app/services/learning_service.py app/api/v1/learning.py app/api/v1/__init__.py
git commit -m "feat(learning): 添加学习进度上报 API"
git push origin integration-day3
```
3. 在群里发：
```
@所有人 M2 已合并！learning API 可用：POST /api/v1/learning/progress
@FE 进度上报接口已就绪，可以开始 VideoPlayer 开发
```
4. 继续执行 BE-A 指令 #2

### 何时执行下一阶段

立即执行 BE-A 指令 #2（视频流验证可以和前端 VideoPlayer 开发并行）

---

## BE-A 指令 #2 — 验证视频 Range 流播放

**🕐 执行时间**：11:00（learning API 提交后）

### 复制给 Claude

```
帮我验证在线教育平台的视频 Range 流播放功能是否正常工作。

需要检查：
1. app/api/v1/courseware.py 中是否有视频流端点（返回 206 Partial Content 的）
2. 如果有，测试 Range 请求：
   curl -H "Range: bytes=0-1023" http://localhost:8000/api/v1/courseware/{id}/stream
3. 如果没有视频流端点，参照 CLAUDE.md 决策 3，基于 HTTP Range 实现一个：
   - 解析 Range header
   - 返回 206 Partial Content
   - 设置 Content-Range 和 Accept-Ranges header
4. 准备一个测试视频文件（如果没有，告诉我如何下载 BigBuckBunny 示例视频）
5. 用浏览器测试：直接用 <video> 标签指向视频 URL，看能否正常播放和拖拽进度

项目规范：
- 路由前缀 /api/v1/
- 认证：get_current_user 依赖
- 统一响应体：{ code, data, message }（但视频流这种二进制响应不需要包这个）
```

### 实现什么功能

- 确保视频播放器（video.js）能正常请求视频数据
- HTTP Range 支持断点续播和拖动进度条
- 这是 CLAUDE.md 决策 3 的落地验证

### 完成后如何交接

1. 将测试结果和测试视频路径整理成一句话发到群里：
   **"视频流可用，测试视频在 /static/videos/demo.mp4，Range 请求返回 206 正常，浏览器可播放"**
2. 通知 FE：视频 URL 格式是什么（如 `/api/v1/courseware/{id}/stream`）
3. 之后你的角色转为"协助 FE 联调 VideoPlayer"

### 何时执行下一阶段

无独立指令。BE-A 指令 #2 完成后，你转为支持角色：
- 协助 FE 调试 VideoPlayer（进度上报联调、视频播放异常）
- 16:00 全链路测试时修复自己模块的 Bug

---

# BE-B 角色指令（2 条）

---

## BE-B 指令 #1 — 修复考试批改逻辑 + 补测试

**🕐 执行时间**：09:15（启动会后立即执行）

### 复制给 Claude

```
帮我审查并修复在线教育平台的考试批改逻辑。

背景：
- 考试模型在 app/models/exam.py：Exam（考试表）、ExamRecord（作答记录）、WrongQuestion（错题本）
- 批改逻辑在 app/services/exam_service.py 的 submit_exam() 方法
- 考试流程：POST /exams/{id}/start（开始考试）→ POST /exams/{id}/submit（提交答案）
- 题目表是 questions，考试-题目关联是 exam_questions（含每题分值）
- 题库模型在 app/models/question.py，包含 question_type（single/multiple/text）

需要做的事情：

1. 审计 app/services/exam_service.py 的 submit_exam() 方法：
   - 单选题（single）判分逻辑是否正确（完全匹配才算对）
   - 多选题（multiple）判分逻辑是否正确（部分匹配是否给分？建议完全匹配）
   - 判断题（如果有）判分逻辑是否正确
   - 分数计算是否正确（每题分值 × 正确数）
   - 错题是否正确插入 wrong_questions 表
   - 边界情况：空答案、部分提交、重复提交

2. 编写 tests/test_exam_submit.py，至少包含：
   - test_submit_single_choice_correct（单选题答对）
   - test_submit_single_choice_wrong（单选题答错）
   - test_submit_multiple_choice_correct（多选题答对）
   - test_submit_mixed_answers（混合题型）
   - test_resubmit_rejected（重复提交拒绝）
   测试用 SQLite（参考 tests/conftest.py 的写法）

3. 如果发现 bug，修复后重新运行全量测试确认无回归。

文件路径约定：
- 模型：app/models/
- 服务：app/services/exam_service.py
- 测试：tests/test_exam_submit.py
- conftest 已有 test 框架，参考 tests/test_enroll.py
```

### 实现什么功能

- 确保考试批改逻辑正确（分数计算、错题入库）
- 补充测试覆盖，防止后续改动引入回归
- 这是考试模块的核心逻辑，前端 ExamPage 依赖它返回正确结果

### 完成后如何交接

1. 运行全量测试确认通过：
```bash
conda run -n edu_platform pytest -q
```
2. 提交到集成分支：
```bash
git checkout integration-day3
git pull origin integration-day3
git add app/services/exam_service.py tests/test_exam_submit.py
git commit -m "fix(exam): 修复批改逻辑并补充测试"
git push origin integration-day3
```
3. 在群里发：
```
@所有人 M3 已合并！考试批改修复完成，新增 exam_submit 测试
@FE 考试 API 已可用：POST /exams/{id}/start, POST /exams/{id}/submit, GET /exams/{id}/result
```
4. 继续执行 BE-B 指令 #2

### 何时执行下一阶段

提交后立即执行 BE-B 指令 #2（统计接口优化可以与 FE 开发并行）

---

## BE-B 指令 #2 — 优化统计数据格式

**🕐 执行时间**：11:00（提交考试批改后）

### 复制给 Claude

```
帮我检查并优化在线教育平台的统计数据 API，确保返回格式与前端 ECharts 兼容。

需要检查的端点（在 app/api/v1/stats.py 中）：
1. GET /api/v1/stats/calendar - 学习日历热力图
2. GET /api/v1/stats/duration - 学习时长柱状图
3. GET /api/v1/stats/knowledge-mastery - 知识掌握度雷达图

对每个端点：
- 检查返回的 data 格式是否适合前端直接绑定到 ECharts
- 日历数据格式应为：[{date: "2026-07-18", value: 3600}, ...]
- 时长数据格式应为：[{date: "2026-07-01", duration: 1800}, ...]
- 知识掌握度格式应为：[{knowledge: "知识点名", score: 85}, ...]

如果格式不对，修改 services/stats_service.py 中的对应方法。

同时：
- 确保所有 stats 端点需要认证（get_current_user 依赖）
- 检查是否有 N+1 查询问题
- 用 Postman 测试每个端点，确认返回数据格式正确

项目规范：统一响应体 { code, data, message }，data 内是具体数据
```

### 实现什么功能

- 确保统计 API 返回的数据格式与 ECharts 官方示例兼容
- FE 开发 StatsPage 时直接绑定数据即可渲染图表
- 无需前后端来回调整数据格式

### 完成后如何交接

1. Postman 测试 3 个端点，截图保存
2. 在群里发：
   **"统计 API 格式已对齐 ECharts。示例返回：GET /stats/calendar → [{date:'2026-07-18',value:3600}]，FE 可直接用数据集"**
3. 之后你的角色转为"协助 FE 联调 ExamPage + StatsPage"
4. 将 Postman 测试结果截图发给 FE，帮助他理解 API 返回格式

### 何时执行下一阶段

无独立指令。BE-B 指令 #2 完成后，你转为支持角色：
- 协助 FE 调试 ExamPage（答案提交、结果展示）
- 协助 FE 调试 StatsPage（ECharts 数据绑定）
- 16:00 全链路测试时修复自己模块的 Bug

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

# FE 角色指令（5 条）

> **FE 的指令最重要**，按页面顺序逐个执行。每个页面都是独立指令。

---

## FE 指令 #1 — 课程列表页 CourseList.vue

**🕐 执行时间**：09:15（启动会后立即执行）

### 复制给 Claude

```
帮我在在线教育平台前端项目中开发课程列表页。

项目前端技术栈：
- Vue 3（<script setup>）+ Element Plus + Vue Router + Axios
- 认证：Cookie + CSRF（前端无需手动处理，axios 封装已做）
- API 封装在 src/api/ 目录下
- 路由文件：src/router/index.js
- 统一响应体：{ code: 200, data: { items: [], total, page, page_size }, message: "success" }

请完成以下工作：

1. 创建 src/pages/CourseList.vue，功能包括：
   - 顶部搜索框（Input 组件，输入后点击搜索按钮触发）
   - 课程卡片网格（用 Element Plus Card 组件）
   - 每张卡片显示：课程标题、描述（截取50字）、讲师名、价格、选课人数、状态标签
   - 底部分页（Pagination 组件，每页 12 个）
   - 点击卡片跳转到课程详情 /courses/:id

2. 调用 GET /api/v1/courses?page=1&page_size=12&keyword=xxx
   - 解包统一响应体，提取 data.items 和 data.total
   - 搜索时重置到第 1 页
   - 加载时显示 loading 状态

3. 在 router/index.js 中添加路由：
   { path: '/courses', name: 'courses', component: () => import('@/pages/CourseList.vue') }

参考现有文件：
- src/pages/Home.vue（了解页面结构和 Element Plus 用法）
- src/api/ 目录下的 axios 封装
- src/router/index.js 的路由写法
```

### 实现什么功能

- 课程列表页面：搜索、分页、卡片展示
- 用户可以浏览课程、搜索关键词、翻页查看
- 是全链路的第一步：课程浏览 → 点进去选课 → 学习

### 完成后如何交接

1. 本地测试：`npm run dev`，打开 http://localhost:5173/courses
2. 确认能看到课程列表（需要有演示数据，等 DBA M1 合并后执行脚本）
3. 在群里发：**"CourseList 页面完成，路由 /courses 已配置"**
4. 继续执行 FE 指令 #2

### 何时执行下一阶段

CourseList 完成 + DBA 演示数据可用后，立即执行 FE 指令 #2

---

## FE 指令 #2 — 课程详情页 CourseDetail.vue

**🕐 执行时间**：10:30（CourseList 完成后）

### 复制给 Claude

```
帮我在在线教育平台前端项目中开发课程详情页。

需要创建 src/pages/CourseDetail.vue，功能包括：

1. 课程基本信息区：
   - 课程标题、描述、封面图、讲师、价格、选课人数
   - 选课/退课按钮（根据是否已选课显示不同状态）
   - 调用 GET /api/v1/courses/:id 获取详情
   - 选课：POST /api/v1/courses/:id/enroll
   - 退课：DELETE /api/v1/courses/:id/enroll

2. 章节树区域：
   - 用 Element Plus Collapse 折叠面板展示章节
   - 调用 GET /api/v1/courses/:id/chapters 获取章节树
   - 每个章节可展开查看子章节和课件列表
   - 点击课件跳转到 /learn/:coursewareId

3. 状态处理：
   - 加载中：显示骨架屏或 loading
   - 未登录：自动跳转登录页（路由守卫已处理）
   - 课程不存在：显示"课程不存在"提示
   - 选课成功/失败：显示 Element Plus Message 提示

4. 在 router/index.js 添加路由：
   { path: '/courses/:id', name: 'courseDetail', component: () => import('@/pages/CourseDetail.vue') }

CSS 要求：
- 上半部分课程信息用卡片布局
- 下半部分章节树用折叠面板
- 移动端自适应（单列布局）
```

### 实现什么功能

- 课程详情页：查看课程信息、查看章节结构、选课/退课
- 选课操作后用户可以进入我的课程列表和视频播放
- 这是从"浏览"到"学习"的桥梁

### 完成后如何交接

1. 本地测试：从 CourseList 点击课程 → 进入详情页 → 点击选课
2. 在群里发：**"CourseDetail 完成，选课/退课正常"**
3. 继续执行 FE 指令 #3

### 何时执行下一阶段

CourseDetail 完成 + BE-A learning API 可用（M2）后，执行 FE 指令 #3

---

## FE 指令 #3 — 视频播放器 VideoPlayer.vue

**🕐 执行时间**：11:00（CourseDetail 完成后 + BE-A M2 已合并）

### 复制给 Claude

```
帮我在在线教育平台前端项目中开发视频播放器页面。

需要创建 src/pages/VideoPlayer.vue，功能包括：

1. Video.js 播放器：
   - npm install video.js（如果还没安装）
   - 引入 video.js 和默认样式
   - 初始化播放器，controls: true, fluid: true（自适应宽度）
   - 视频源从路由参数 coursewareId 获取：
     先调 GET /api/v1/chapters/{chapterId}/courseware 获取课件列表
     从课件列表中找到视频 URL

2. 章节导航（左侧或顶部）：
   - 显示当前课程的全部章节（从课程详情缓存或重新请求）
   - 当前播放章节高亮
   - 点击切换章节（切换视频源）

3. 播放进度自动上报：
   - 每 30 秒上报一次
   - 调用 POST /api/v1/learning/progress
   - 请求体：{ courseware_id, progress: 当前进度%, duration: 累计秒数 }
   - 暂停时也上报一次
   - 切换章节时上报当前章节最终进度

4. 下一章节按钮：
   - 当前章节播放完毕时显示"下一章"按钮
   - 点击切换视频源并重新开始进度上报

5. 在 router/index.js 添加路由：
   { path: '/learn/:coursewareId', name: 'learn', component: () => import('@/pages/VideoPlayer.vue') }

技术要求：
- video.js 用最简配置，不要复杂皮肤
- 进度上报失败不影响播放（console.error 即可）
- 页面卸载时清理定时器和 video.js 实例
```

### 实现什么功能

- 视频播放页面：播放视频、章节切换、自动上报进度
- 这是核心学习闭环的关键一环
- 播放进度上报到后端 → 统计页面可展示学习时长

### 完成后如何交接

1. 本地测试：从课程详情点击课件 → 进入播放器 → 播放几秒 → 检查网络请求中是否有 learning/progress 调用
2. 在群里发：**"VideoPlayer 完成，进度上报正常"**
3. 继续执行 FE 指令 #4

### 何时执行下一阶段

VideoPlayer 完成 + BE-B M3 已合并后，执行 FE 指令 #4

---

## FE 指令 #4 — 考试列表 + 答题页

**🕐 执行时间**：13:30（午休后 + BE-B M3 已合并）

### 复制给 Claude

```
帮我在在线教育平台前端项目中开发考试模块（2 个页面）。

需要创建：

═══════════════════
一、ExamList.vue — 考试列表
═══════════════════
- 调用 GET /api/v1/exams 获取考试列表
- Element Plus Card 展示每场考试：标题、时长(分钟)、题数、状态标签
- 状态标签颜色：draft=灰色, published=绿色, closed=红色
- 只有 published 状态的考试显示"开始考试"按钮
- 已提交过的考试显示"查看成绩"按钮（判断逻辑：调用 /my/exam-records 检查）
- 分页 Pagination

═══════════════════
二、ExamPage.vue — 答题页
═══════════════════
路由参数：/exams/:id

流程：
1. 进入页面调 POST /api/v1/exams/:id/start 开始考试
2. 获取考试信息（题目列表、总时长、总分）
3. 显示倒计时（剩余时间 = 考试时长，用 setInterval 每秒更新）

4. 题目渲染（根据 question_type 切换）：
   - single（单选）：<el-radio-group v-model="answers[qid]">
   - multiple（多选）：<el-checkbox-group v-model="answers[qid]">
   - text（简答）：<el-input type="textarea" v-model="answers[qid]">

5. 答题卡（右侧或底部）：
   - 显示题目序号列表（1, 2, 3...）
   - 已答题目标绿色，未答标灰色
   - 点击序号跳转到对应题目

6. 提交：
   - "提交"按钮 + 二次确认 Dialog
   - 调用 POST /api/v1/exams/:id/submit
   - 请求体：{ answers: { "题目ID": "答案值" } }
   - 提交成功后跳转到结果展示

7. 结果展示：
   - 提交成功后显示：总分、正确数、正确率
   - 每题显示你的答案 + 正确答案（绿色=对，红色=错）

8. 边界处理：
   - 倒计时到 0 自动提交
   - 页面刷新时提示"考试进行中，离开将丢失进度"
   - 重复 start 提示"考试已开始"

═══════════════════
三、路由
═══════════════════
{ path: '/exams', name: 'exams', component: () => import('@/pages/ExamList.vue') },
{ path: '/exams/:id', name: 'examPage', component: () => import('@/pages/ExamPage.vue') }
```

### 实现什么功能

- 完整的在线考试体验：考试列表 → 开始考试 → 答题 → 提交 → 查看成绩
- 倒计时、答题卡、题型渲染、自动批改
- 这是学习闭环的"验证"环节

### 完成后如何交接

1. 本地测试：ExamList → 点击考试 → 答几道题 → 提交 → 查看成绩
2. 在群里发：**"考试模块完成，答题+成绩展示正常"**
3. 继续执行 FE 指令 #5（最后一条）

### 何时执行下一阶段

ExamList + ExamPage 完成后，立即执行 FE 指令 #5

---

## FE 指令 #5 — 学习统计页 StatsPage.vue

**🕐 执行时间**：14:30（考试模块完成后）

### 复制给 Claude

```
帮我在在线教育平台前端项目中开发学习统计页面。

需要创建 src/pages/StatsPage.vue，功能包括：

1. 学习日历热力图：
   - npm install echarts（如果还没安装）
   - 调用 GET /api/v1/stats/calendar
   - 使用 ECharts Calendar 图表（官方示例：https://echarts.apache.org/examples/zh/editor.html?c=calendar-simple）
   - 数据映射：API 返回 [{date: "2026-07-18", value: 3600}, ...]
   - value 转换为小时显示（除以 3600）

2. 学习时长柱状图：
   - 调用 GET /api/v1/stats/duration
   - 使用 ECharts Bar 图表
   - X 轴=日期，Y 轴=学习时长（小时）

3. 知识掌握度雷达图（可选，时间不够可跳过）：
   - 调用 GET /api/v1/stats/knowledge-mastery
   - 使用 ECharts Radar 图表

4. 页面布局：
   - 顶部：用户学习概览卡片（总学习时长、学习天数、平均每日时长）
   - 左侧：日历热力图
   - 右侧：柱状图
   - 底部：雷达图（可选）

5. 在 router/index.js 添加路由：
   { path: '/stats', name: 'stats', component: () => import('@/pages/StatsPage.vue') }

技术要求：
- ECharts 图表响应式（窗口 resize 时自动调整）
- 数据加载前显示 loading
- 如果没有数据，显示"暂无学习数据"空状态
- 复制官方示例后只改数据绑定，不改样式配置
```

### 实现什么功能

- 学习统计页面：日历热力图 + 学习时长柱状图 + 知识掌握度雷达图
- 用户可以看到自己的学习行为可视化
- 这是最终演示的"成果展示"页面

### 完成后如何交接

1. 本地测试：访问 /stats → 确认图表能正常渲染
2. 提交所有前端文件：
```bash
git checkout integration-day3
git pull origin integration-day3

git add frontend/src/pages/CourseList.vue \
        frontend/src/pages/CourseDetail.vue \
        frontend/src/pages/VideoPlayer.vue \
        frontend/src/pages/ExamList.vue \
        frontend/src/pages/ExamPage.vue \
        frontend/src/pages/StatsPage.vue \
        frontend/src/router/index.js

git commit -m "feat(frontend): 完成 6 个核心业务页面"
git push origin integration-day3
```
3. 在群里发：
```
@所有人 M5 已合并！前端 6 个页面全部完成
页面路由：
  /courses - 课程列表
  /courses/:id - 课程详情
  /learn/:id - 视频播放
  /exams - 考试列表
  /exams/:id - 答题
  /stats - 学习统计
```
4. 之后你的工作：配合 PM 全链路测试，修复发现的 UI Bug

### 何时执行下一阶段

所有页面提交后，等待 PM 主导全链路测试，修复测试中发现的 Bug。

---

# PM 角色指令（贯穿全天）

## PM 指令 #1 — 环境验证与看板搭建

**🕐 执行时间**：09:15（启动会后立即执行）

### 复制给 Claude

```
我是在线教育平台的 PM，需要在开发开始前验证环境并搭建管理看板。

请帮我：

1. 启动全栈环境：
   - cd 到项目根目录
   - docker compose up -d mysql redis chromadb（基础设施）
   - 确认 3 个容器都在 running
   - cd backend && conda run -n edu_platform uvicorn app.main:app --reload &
   - cd frontend && npm run dev &
   - 验证：curl http://localhost:8000/health
   - 验证：curl http://localhost:5173

2. 验证后端 69 条 API：
   - 从 app.main 导入 app，列出所有路由
   - 按模块分组统计（auth/courses/enroll/exams/qa/stats 等）
   - 输出路由数量和模块分布

3. 检查前端基础状态：
   - 确认 3 个已有页面（Home/Login/Register）可正常渲染
   - 确认路由守卫工作正常（未登录跳转 /login）

4. 创建团队成员任务追踪表（输出 markdown 格式）：
   | 角色 | 姓名 | M1 | M2 | M3 | M4 | M5 | 备注 |
   |------|------|----|----|----|----|----|------|

5. 发送启动通知到群里的模板：
   "今日集成开发已启动
   集成分支：integration-day3
   文档：集成分支开发指南.md + 团队成员ClaudeCode参考指令.md
   环境：http://localhost:8000 (后端) / http://localhost:5173 (前端)
   数据库：mysql -h 127.0.0.1 -u root -p learning_platform"
```

### 实现什么功能

- 确保全栈环境可用，所有开发者可以开始工作
- 69 条 API 验证通过 → 后端不是瓶颈
- 任务追踪表让 PM 在每个站会时快速更新状态

### 完成后如何交接

1. 将任务追踪表发布到群里
2. 将启动通知发到群里
3. 执行 PM 指令 #2

### 何时执行下一阶段

等 DBA 提交 M1（约 10:30），拉取最新代码执行演示数据脚本

---

## PM 指令 #2 — 验收 M1+DBA 演示数据

**🕐 执行时间**：10:30（等 DBA M1 合并后）

### 复制给 Claude

```
DBA 已经提交了演示数据生成脚本，帮我验收。

请帮我：

1. 拉取最新代码并执行脚本：
   git checkout integration-day3
   git pull origin integration-day3
   conda run -n edu_platform python scripts/generate_demo_data.py

2. 验证数据完整性：
   - 连接 MySQL，统计各表行数：
     SELECT COUNT(*) FROM users;          # 应该是 10
     SELECT COUNT(*) FROM courses;        # 应该是 5
     SELECT COUNT(*) FROM chapters;       # 应该是 15+
     SELECT COUNT(*) FROM courseware;     # 应该是 30+
     SELECT COUNT(*) FROM enrollments;    # 应该是 10-15
     SELECT COUNT(*) FROM questions;      # 应该是 30
     SELECT COUNT(*) FROM exams;          # 应该是 5
   - 输出一个数据盘点表

3. 用测试账号登录验证：
   - student1 / 123456
   - teacher1 / 123456
   - 确认登录成功并返回 cookie

4. 在群里发验收报告：
   "M1 验收通过 ✓
   演示数据已生成：10用户/5课程/30题目/5考试/模拟学习记录
   测试账号：student1/123456, teacher1/123456"
```

### 实现什么功能

- 验收 DBA 的演示数据质量
- 确保后续所有开发和测试都基于真实数据

### 完成后如何交接

1. 在群里发验收报告
2. 在追踪表上标记 DBA M1 完成
3. 等待 BE-A M2 提交（约 11:00）

### 何时执行下一阶段

BE-A M2 合并后，执行 PM 指令 #3

---

## PM 指令 #3 — 验收 M2+协助 FE 联调

**🕐 执行时间**：11:00（BE-A M2 合并后）

### 复制给 Claude

```
BE-A 提交了学习进度 API，帮我验收。

请帮我：

1. Postman/curl 测试 POST /api/v1/learning/progress：
   - 先用 student1 登录获取 cookie
   - 发送进度上报请求：{"courseware_id":1,"progress":45,"duration":30}
   - 确认返回 code: 200
   - 查询数据库确认 learning_records 表有新记录

2. 通知 FE：
   "学习进度 API 就绪，POST /api/v1/learning/progress
   请求体：{courseware_id, progress(0-100), duration(秒)}
   请开始 VideoPlayer 开发"

3. 在追踪表更新 BE-A M2 完成

4. 然后帮我整理当前所有可用的 API 端点清单（按模块分组），
   附上请求体和响应示例，发给 FE 参考
```

### 实现什么功能

- 验收 learning API
- 通知 FE 可以开始 VideoPlayer 开发
- 整理全部 API 文档给 FE

### 完成后如何交接

1. 在群里发 API 清单
2. 在追踪表更新状态
3. 等待 BE-B M3（约 12:00），期间监控 FE 进度

### 何时执行下一阶段

BE-B M3 合并后 + 午休结束后，执行 PM 指令 #4

---

## PM 指令 #4 — 全链路验收 + 部署 + 演示准备

**🕐 执行时间**：16:00（所有节点合并后）

### 复制给 Claude

```
我是 PM，所有开发节点已合并，现在需要做最终验收和部署准备。

请帮我：

1. 全链路端到端测试（完整流程）：
   用 curl 或编写一个 shell 脚本：
   a. 注册新用户：POST /api/v1/auth/register
   b. 登录：POST /api/v1/auth/login
   c. 浏览课程：GET /api/v1/courses
   d. 查看课程详情：GET /api/v1/courses/1
   e. 选课：POST /api/v1/courses/1/enroll
   f. 查看我的课程：GET /api/v1/my/courses
   g. 上报学习进度：POST /api/v1/learning/progress
   h. 查看考试列表：GET /api/v1/exams
   i. 开始考试：POST /api/v1/exams/1/start
   j. 提交考试：POST /api/v1/exams/1/submit
   k. 查看统计：GET /api/v1/stats/calendar, GET /api/v1/stats/duration
   每个步骤检查返回 code 是否为 200，记录失败的步骤

2. 前端页面验证：
   - http://localhost:5173 首页
   - http://localhost:5173/courses 课程列表
   - http://localhost:5173/courses/1 课程详情
   - http://localhost:5173/exams 考试列表
   - http://localhost:5173/stats 统计页面
   检查每个页面是否正常渲染，有无 console 报错

3. Docker Compose 部署验证：
   - docker compose down
   - docker compose up -d
   - 确认所有容器（mysql/redis/chromadb/backend/frontend）都是 running
   - 再次验证 http://localhost:8000/health 和 http://localhost:5173

4. 生成验收报告：
   - 通过的测试步骤
   - 失败的步骤（附错误信息）
   - 前端页面状态（正常/异常）
   - 需要修复的问题清单

5. 准备演示流程清单（最终演示用）：
   1. 打开 http://localhost:5173
   2. 用 student1/123456 登录
   3. 浏览课程列表 → 进入课程详情 → 选课
   4. 进入视频播放页面（如果有课件）
   5. 浏览考试列表 → 参加考试 → 提交
   6. 查看学习统计
   7. 切换到 Postman 演示 RAG 问答
   8. 展示 Swagger 文档 http://localhost:8000/docs
```

### 实现什么功能

- 完整端到端测试，验证所有节点合并后功能可用
- Docker 一键部署验证
- 生成演示流程清单供最终演示使用

### 完成后如何交接

1. 将验收报告中的 Bug 清单发给对应开发者
2. 修复完成后重新跑一次全链路测试
3. 17:00 组织全员演示彩排
4. 彩排通过后宣布交付完成

### 何时执行下一阶段

演示彩排通过 → 宣布交付完成 → 撰写今日总结 → 合并到 dev

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
