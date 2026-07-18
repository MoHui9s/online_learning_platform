# 团队成员（DBA） Claude Code 参考指令手册

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
