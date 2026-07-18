# 6人团队并行执行计划

---

## 一、团队分工与并行任务分配

### 角色职责表

| 角色 | 姓名/代号 | 主要职责 | 关键产出 |
|------|----------|---------|---------|
| **PM** | Project Manager | 协调、验收、部署、演示准备 | 环境部署、演示数据、验收报告 |
| **FE** | Frontend Dev | 全部前端页面开发 | 6个核心页面 |
| **BE-A** | Backend Dev A | 学习进度模块 + 课件视频流 | learning API + 视频Range流验证 |
| **BE-B** | Backend Dev B | 考试批改优化 + 统计数据 | 批改逻辑完善 + 统计聚合 |
| **BE-C** | Backend Dev C | RAG演示准备 + 知识库构建 | ChromaDB数据 + Postman集合 |
| **DBA** | Database Admin | 数据库优化 + 测试数据 | 索引优化 + 演示数据脚本 |

---

## 二、并行工作流程图

```
时间轴    PM              FE                BE-A            BE-B            BE-C            DBA
────────────────────────────────────────────────────────────────────────────────────────────
09:00   启动会(15min)    ─────────────────  全员参加  ─────────────────────────────────────
        │
09:15   环境检查        │                  │              │              │              │
        Docker启动      │                  │              │              │              │
        │               ▼                  ▼              ▼              ▼              ▼
09:30   ├─监控─────→   课程列表页      学习进度API    考试批改优化   RAG数据准备    索引分析
        │               ├CourseList      ├learning.py   ├exam优化      ├知识库构建    ├explain
        │               │                │              │              │              │
10:30   ├─协调FE/BE─→  课程详情页      视频流验证     统计聚合接口   Postman集合    测试数据
        │               ├CourseDetail    ├Range测试     ├stats优化     ├API文档       ├SQL脚本
        │               │                │              │              │              │
12:00   午休           ──────────────────  全员午休  ──────────────────────────────────────
        │
13:00   ├─联调准备───→ 视频播放器      API联调        API联调        演示脚本       数据验证
        │               ├VideoPlayer     ├进度上报      ├测试修复      ├SSE测试       ├数据检查
        │               │                │              │              │              │
14:30   ├─验收P0────→  考试模块         └─完成交付─┐   └─完成交付─┐  └─完成交付─┐  └─完成交付─┐
        │               ├ExamList         协助FE联调│    协助FE联调│   协助FE联调│   协助FE联调│
        │               ├ExamPage         ↓           ↓            ↓            ↓
15:30   ├─验收P1────→  学习统计页       ─────────  全员联调 + Bug修复  ──────────────────
        │               └StatsPage
        │               
16:00   ├─全链路测试─→ ─────────────────  PM主导端到端测试  ────────────────────────
        │               注册→选课→播放→考试→统计 完整流程
        │
16:30   Docker部署     ─────────────────  PM + DBA 执行部署  ────────────────────────
        docker-compose up -d 验证
        │
17:00   演示预演        ─────────────────  全员参加演示彩排  ────────────────────────
        └完成交付
```

---

## 三、各角色详细任务清单

### PM（Project Manager）- 8小时

#### 阶段1：启动与环境准备（09:00-09:30）
- [ ] 召开启动会，同步方案（15分钟）
- [ ] 检查 Docker 服务状态（MySQL/Redis/ChromaDB）
- [ ] 验证后端 69 条 API 可用性
- [ ] 创建任务看板（GitHub Projects 或飞书）

#### 阶段2：协调与监控（09:30-14:30）
- [ ] 每小时询问各角色进度
- [ ] 协调 FE 与 BE-A 的接口对接（学习进度 API）
- [ ] 验收 BE-A/B/C 交付的 API（Postman 测试）
- [ ] 协助解决阻塞问题

#### 阶段3：联调与测试（14:30-16:30）
- [ ] 主导全链路测试：注册 → 选课 → 播放 → 考试 → 统计
- [ ] 记录 Bug 清单，分配给对应开发者
- [ ] 验证修复结果

#### 阶段4：部署与交付（16:30-17:00）
- [ ] 与 DBA 一起执行 Docker Compose 部署
- [ ] 验证生产环境可用性
- [ ] 组织演示彩排

---

### FE（Frontend Developer）- 8小时

#### 阶段1：课程模块（09:15-10:30，1.25h）
**任务1: 课程列表页** `src/pages/CourseList.vue`
- [ ] 调用 GET /api/v1/courses 获取课程列表
- [ ] Element Plus Table 展示（标题、讲师、价格、状态）
- [ ] Pagination 分页组件
- [ ] 搜索框（关键词筛选）
- [ ] 点击跳转详情页

#### 阶段2：课程详情与选课（10:30-12:00，1.5h）
**任务2: 课程详情页** `src/pages/CourseDetail.vue`
- [ ] 调用 GET /api/v1/courses/:id 获取课程信息
- [ ] 调用 GET /api/v1/courses/:id/chapters 获取章节树
- [ ] Collapse 折叠面板展示章节
- [ ] 选课/退课按钮（POST/DELETE /api/v1/courses/:id/enroll）
- [ ] 点击章节跳转播放页

#### 阶段3：视频播放器（13:00-14:30，1.5h）
**任务3: 视频播放器页** `src/pages/VideoPlayer.vue`
- [ ] 安装 video.js: npm install video.js
- [ ] 初始化播放器（最简配置）
- [ ] 左侧章节导航（TreeSelect）
- [ ] 播放进度上报（每30秒调 POST /api/v1/learning/progress）
- [ ] 下一章节按钮

#### 阶段4：考试模块（14:30-15:30，1h）
**任务4: 考试列表** `src/pages/ExamList.vue`
- [ ] 调用 GET /api/v1/exams 获取考试列表
- [ ] Card 卡片展示（标题、时长、题数）
- [ ] 点击跳转答题页

**任务5: 答题页** `src/pages/ExamPage.vue`
- [ ] 调用 POST /api/v1/exams/:id/start 开始考试
- [ ] 单题渲染（RadioGroup / CheckboxGroup）
- [ ] 答案收集（v-model 绑定）
- [ ] 提交按钮（POST /api/v1/exams/:id/submit）
- [ ] 结果页（分数、正确率）

#### 阶段5：学习统计（15:30-16:00，0.5h）
**任务6: 学习统计页** `src/pages/StatsPage.vue`
- [ ] 安装 ECharts: npm install echarts
- [ ] 调用 GET /api/v1/stats/calendar 获取学习日历数据
- [ ] 绘制热力图（复制官方 Calendar 示例）
- [ ] 如时间充裕，添加柱状图（学习时长）

#### 阶段6：联调与修复（16:00-17:00）
- [ ] 配合 PM 完成全链路测试
- [ ] 修复发现的 Bug
- [ ] 优化 UI 细节

---

### BE-A（Backend Developer A）- 学习进度模块

#### 任务1: 学习进度上报 API（09:15-10:30，1.25h）

**步骤1**: 创建 Schema
文件: `backend/app/schemas/learning.py`（新建）

```python
from pydantic import BaseModel, Field

class ProgressUpdate(BaseModel):
    courseware_id: int = Field(..., description="课件ID")
    progress: int = Field(..., ge=0, le=100, description="播放进度百分比")
    duration: int = Field(..., ge=0, description="本次学习时长(秒)")
```

**步骤2**: 创建 Service
文件: `backend/app/services/learning_service.py`（新建）

```python
from sqlalchemy.orm import Session
from app.models.learning import LearningRecord, LearningCalendar
from datetime import datetime, date

def update_progress(
    db: Session, 
    user_id: int, 
    courseware_id: int, 
    progress: int, 
    duration: int
):
    # 查找或创建学习记录
    record = db.query(LearningRecord).filter_by(
        user_id=user_id, 
        courseware_id=courseware_id
    ).first()
    
    if not record:
        record = LearningRecord(
            user_id=user_id,
            courseware_id=courseware_id,
            progress=progress,
            duration=duration
        )
        db.add(record)
    else:
        record.progress = progress
        record.duration += duration
        record.last_learn_at = datetime.now()
    
    # 更新学习日历
    today = date.today()
    calendar = db.query(LearningCalendar).filter_by(
        user_id=user_id,
        learn_date=today
    ).first()
    
    if not calendar:
        calendar = LearningCalendar(
            user_id=user_id,
            learn_date=today,
            duration=duration
        )
        db.add(calendar)
    else:
        calendar.duration += duration
    
    db.commit()
```

**步骤3**: 创建路由
文件: `backend/app/api/v1/learning.py`（新建）

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.learning import ProgressUpdate
from app.schemas.common import success
from app.services import learning_service

router = APIRouter(prefix="/learning", tags=["learning"])

@router.post("/progress")
def update_progress(
    payload: ProgressUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learning_service.update_progress(
        db, current.id, payload.courseware_id, 
        payload.progress, payload.duration
    )
    return success(message="进度已保存")
```

**步骤4**: 挂载路由
文件: `backend/app/api/v1/__init__.py`

```python
# 添加导入
from app.api.v1 import learning

# 在 api_router 中添加
api_router.include_router(learning.router)
```

**验收**: 用 Postman 测试
```json
POST http://localhost:8000/api/v1/learning/progress
Cookie: access_token=xxx; csrf_token=xxx
Headers: X-CSRF-Token: xxx

Body:
{
  "courseware_id": 1,
  "progress": 45,
  "duration": 30
}
```

#### 任务2: 视频 Range 流验证（10:30-12:00，1.5h）
- [ ] 准备测试视频文件（BigBuckBunny.mp4 或任意 mp4）
- [ ] 测试 GET /api/v1/courseware/:id/stream 的 HTTP Range 响应
- [ ] 用 curl 验证: `curl -H "Range: bytes=0-1023" http://localhost:8000/api/v1/courseware/1/stream`
- [ ] 用浏览器 video 标签验证播放
- [ ] 与 FE 对齐视频 URL 格式

#### 任务3: 联调与支持（13:00-17:00）
- [ ] 协助 FE 调试学习进度上报
- [ ] 协助 FE 调试视频播放
- [ ] 修复发现的 Bug

---

### BE-B（Backend Developer B）- 考试与统计优化

#### 任务1: 考试批改逻辑检查（09:15-11:00，1.75h）
文件: `backend/app/services/exam_service.py`

检查清单:
- [ ] submit_exam() 方法是否正确计算分数
- [ ] 单选题判分逻辑（answer == correct_answer）
- [ ] 多选题判分逻辑（set(answer) == set(correct_answer)）
- [ ] 判断题判分逻辑
- [ ] 错题本插入逻辑（只插入答错的题目）
- [ ] exam_records 表正确记录分数和状态

编写单元测试: `backend/tests/test_exam_submit.py`
```python
def test_submit_exam_single_choice():
    # 测试单选题批改
    pass

def test_submit_exam_multiple_choice():
    # 测试多选题批改
    pass

def test_wrong_questions_insert():
    # 测试错题本插入
    pass
```

#### 任务2: 统计数据聚合优化（11:00-12:00，1h）
文件: `backend/app/services/stats_service.py`

优化接口:
- [ ] get_calendar() - 返回格式: `[{"date": "2026-07-18", "value": 3600}, ...]`
- [ ] get_duration() - 返回格式: `[{"date": "2026-07-01", "duration": 1800}, ...]`
- [ ] get_knowledge_mastery() - 返回格式: `[{"knowledge": "机器学习", "score": 85}, ...]`

确保数据格式与 ECharts 兼容。

#### 任务3: API 测试（13:00-14:30，1.5h）
- [ ] Postman 测试全部 exam 接口（/exams, /exams/:id/start, /exams/:id/submit）
- [ ] Postman 测试全部 stats 接口（/stats/calendar, /stats/duration, /stats/knowledge-mastery）
- [ ] 导出 Postman Collection: `docs/postman/Exam-Stats-APIs.json`
- [ ] 更新 Swagger 文档注释

#### 任务4: 联调与支持（14:30-17:00）
- [ ] 协助 FE 调试考试模块
- [ ] 协助 FE 调试统计模块
- [ ] 修复发现的 Bug

---

### BE-C（Backend Developer C）- RAG 演示准备

#### 任务1: 知识库数据构建（09:15-11:00，1.75h）
- [ ] 启动 ChromaDB: `docker compose up -d chromadb`
- [ ] 准备演示用 PDF 文档（3-5 个课程相关资料，如机器学习教程.pdf）
- [ ] 调用 POST /api/v1/courses/:id/knowledge-base/build 构建知识库
- [ ] 验证向量数据已存入 ChromaDB（检查 chroma_data 目录）
- [ ] 测试检索效果（curl 调用问答接口）

#### 任务2: Postman 演示集合（11:00-12:00，1h）
创建文件: `docs/postman/RAG-Demo.postman_collection.json`

包含接口:
1. **知识库构建**
   ```
   POST /api/v1/courses/:id/knowledge-base/build
   Body: { "file_path": "path/to/document.pdf" }
   ```

2. **流式问答**
   ```
   POST /api/v1/qa/ask
   Body: { "course_id": 1, "question": "什么是机器学习？" }
   注意: 响应是 SSE 流，Postman 会显示为文本流
   ```

3. **问答历史**
   ```
   GET /api/v1/qa/history?course_id=1&page=1&page_size=20
   ```

4. **相似题推荐**
   ```
   POST /api/v1/assistant/similar-questions
   Body: { "question_id": 1, "limit": 5 }
   ```

添加详细说明文档。

#### 任务3: SSE 流式测试脚本（13:00-14:30，1.5h）
创建文件: `backend/scripts/test_sse.py`

```python
import requests

url = "http://localhost:8000/api/v1/qa/ask"
data = {"course_id": 1, "question": "什么是机器学习？"}
cookies = {"access_token": "YOUR_TOKEN"}

with requests.post(url, json=data, cookies=cookies, stream=True) as r:
    print("开始接收 SSE 流：")
    for line in r.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            print(decoded)
```

- [ ] 编写测试脚本
- [ ] 录制终端演示视频
- [ ] 准备演示话术

#### 任务4: 联调与演示准备（14:30-17:00）
- [ ] 准备演示数据（5 个典型问题 + 回答）
- [ ] 与 PM 对齐演示流程
- [ ] 彩排 RAG 演示环节

---

### DBA（Database Admin）- 数据库优化与测试数据

#### 任务1: 索引分析与优化（09:15-10:30，1.25h）
```sql
-- 连接数据库
mysql -h 127.0.0.1 -u root -p learning_platform

-- 检查现有索引
SHOW INDEX FROM courses;
SHOW INDEX FROM enrollments;

-- 添加复合索引
CREATE INDEX idx_enrollments_user_course ON enrollments(user_id, course_id);
CREATE INDEX idx_learning_records_user_courseware ON learning_records(user_id, courseware_id);

-- 验证索引效果
EXPLAIN SELECT * FROM enrollments WHERE user_id = 1;
```

#### 任务2: 测试数据生成脚本（10:30-12:00，1.5h）
创建文件: `backend/scripts/generate_demo_data.py`

生成内容:
- 10 个用户（5 学生 + 5 老师）
- 5 个课程（每个 3-5 章节）
- 每章 2-3 个课件（含视频）
- 20 个知识点
- 50 个题目
- 5 个考试
- 模拟学习记录

#### 任务3: 数据库备份（13:00-14:00，1h）
```bash
# 导出数据
mysqldump -h 127.0.0.1 -u root -p learning_platform > backup.sql

# 测试恢复
mysql -h 127.0.0.1 -u root -p learning_platform < backup.sql
```

#### 任务4: 性能监控与支持（14:00-17:00）
- [ ] 监控数据库连接数
- [ ] 监控慢查询
- [ ] 协助排查 Bug
- [ ] 协助 Docker 部署

---

## 四、关键里程碑

### M1: 后端就绪（12:00）
- [ ] BE-A: 学习进度 API 可用
- [ ] BE-B: 考试批改测试通过
- [ ] BE-C: 知识库已构建
- [ ] DBA: 演示数据已生成

### M2: 前端 P0 完成（14:30）
- [ ] CourseList 可展示
- [ ] CourseDetail 可选课
- [ ] VideoPlayer 可播放

### M3: 前端 P1 完成（16:00）
- [ ] ExamList 可展示
- [ ] ExamPage 可答题
- [ ] StatsPage 有图表

### M4: 全链路联调（16:30）
- [ ] 注册→选课→播放→考试→统计 全通

### M5: 部署就绪（17:00）
- [ ] Docker Compose 成功
- [ ] 演示彩排通过

---

## 五、沟通协议

### 站会时间
- 10:30 / 12:30 / 14:30 / 16:30（每次5分钟）

### 阻塞升级
- 立即 @PM 协调

### 代码提交
- 每完成一个任务提交一次
- 遵循 Conventional Commits

---

## 六、风险应对

| 风险 | 概率 | 应对 |
|------|------|------|
| FE 开发超时 | 高 | 砍掉 P1，只保留 P0 |
| video.js 问题 | 中 | 最简配置 |
| Docker 部署失败 | 低 | 本地开发模式演示 |

---

## 七、演示脚本（17:00）

### 流程（10分钟）
1. 注册登录（1分钟）
2. 浏览选课（1分钟）
3. 观看视频（2分钟）+ 展示数据库记录
4. 参加考试（2分钟）
5. 查看统计（1分钟）
6. RAG演示（2分钟）Postman
7. 后台展示（1分钟）Swagger + DB

### 话术
> "这是我们8小时完成的在线教育平台MVP，涵盖完整学习闭环。"
> "技术栈：Vue 3 + FastAPI + MySQL + LangChain。"
> "后端69条API全可用，前端6个核心页面。"

---

## 八、交付清单

### 代码
- [ ] 前端 6 个页面
- [ ] 后端 learning 模块
- [ ] 数据库脚本

### 文档
- [ ] Swagger API 文档
- [ ] Postman Collection
- [ ] 演示脚本

### 环境
- [ ] Docker Compose 配置
- [ ] 演示数据已加载

---

## 九、成功标准

### P0（最小）
- ✅ 注册/登录
- ✅ 选课
- ✅ 播放视频
- ✅ 进度上报

### P0+P1（完整）
- 上述 +
- ✅ 考试
- ✅ 统计

---

## 十、紧急预案

### A: FE严重超时（14:00）
砍掉P1，专注P0

### B: Docker失败（16:30）
本地开发模式演示

### C: 视频播放失败（15:00）
使用公网CDN视频

---

**立即开始执行！**
