# 团队成员（BE-A） Claude Code 参考指令手册

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
