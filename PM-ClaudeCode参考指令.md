# 团队成员（PM） Claude Code 参考指令手册

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
