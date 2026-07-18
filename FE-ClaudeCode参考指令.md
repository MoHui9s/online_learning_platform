# 团队成员（FE） Claude Code 参考指令手册

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
