# 团队成员（BE-B） Claude Code 参考指令手册

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
