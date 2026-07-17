# CLAUDE.md — 在线教育学习平台 · 全员施工规范

> 本文件是全团队（含 Claude Code）的施工总纲。**四个关键决策**与 **API 规范**为强约束，任何代码不得违背。
> 子目录另有 `backend/CLAUDE.md`、`frontend/CLAUDE.md` 承接分层细则。
> 团队成员用 Claude Code 开发时：先读本文件「关键决策 / API 规范 / 团队分工」，再读对应分层文件，最后动手。

## 1. 项目概览

综合性在线教育学习平台：课程管理、在线学习、智能答疑（RAG）、AI 学习助手、考试测评、学习分析。
前后端分离，Docker Compose 编排。团队 6 人（PM×1、FE×1、BE-A/B/C×3、DBA/运维×1），10 个工作日。

- 仓库：https://github.com/MoHui9s/online_learning_platform.git
- 后端：`backend/`（FastAPI）　前端：`frontend/`（Vue 3）　文档：`docs/`

## 2. 技术栈（版本以此为准）

| 层 | 技术 |
|----|------|
| 前端 | Vue 3.4+、Vite 5、Element Plus 2.6+、Pinia、Vue Router、Axios、video.js、ECharts |
| 后端 | Python 3.11+、FastAPI 0.110+、SQLAlchemy 2.0、Alembic、Pydantic v2、python-jose、passlib[bcrypt] |
| AI | LangChain **0.2.16**、ChromaDB **0.5.3**（客户端与镜像同版本，见决策 4）、OpenAI 兼容接口（可切 Ollama） |
| 数据 | MySQL 8.0、Redis 7.0、ChromaDB（持久化） |
| 部署 | Docker 24+、Docker Compose 2.20+ |

## 3. 四个已锁定的关键决策（强约束，勿违背）

### 决策 1 — 认证：JWT 存 HttpOnly Cookie + CSRF 双提交 token
- access_token / refresh_token 均以 **HttpOnly Cookie** 下发，防 XSS 窃取。
- 前端**不手动加 `Authorization` header**，浏览器自动携带 cookie。
- **写操作（POST/PUT/DELETE/PATCH）**必须带 `X-CSRF-Token` header，值取自后端下发的可读 `csrf_token` cookie（双提交校验）。
- **SSE 走原生 `EventSource`**，依赖 cookie 自动鉴权 —— 这是选 Cookie 而非 Bearer 的**主因**（EventSource 无法设置自定义 header）。
- 必备接口：`/auth/refresh`（刷新 access）、`/auth/logout`（清除 cookie）。
- 详见 `docs/decisions/auth.md`。

### 决策 2 — 异步：MVP 用 FastAPI BackgroundTasks
- 视频「二期转码」/ 文档解析 / 知识库构建等后台任务，MVP 阶段统一用 `BackgroundTasks`。
- **不引入 Celery**（列为二期）。不要在 MVP 里加 Celery/broker 依赖。

### 决策 3 — 视频：MVP 用 HTTP Range 字节流
- 后端用 **HTTP Range 请求**直出视频字节流，video.js 原生支持断点续播/倍速。
- **不做 HLS 转码**（`.m3u8`/多码率列为二期）。

### 决策 4 — RAG 版本钉定：chromadb 全家 0.5.3，客户端=镜像同版本
- `chromadb`（pip 客户端）与 `chromadb/chroma`（Docker 镜像）**统一钉 0.5.3**，langchain 全家钉 0.2.x（精确版本见 `backend/requirements.txt`，勿自行升级）。
- 背景：原定 0.5.5 被 `langchain-chroma` 全系列**显式拉黑**（`!=0.5.4, !=0.5.5`，该版本客户端有已知缺陷），pip 无解冲突；0.5.3 是黑名单外、两端都有发行版的最近版本。
- **禁止**引入 langchain / chromadb 1.x（API 不兼容 0.2/0.5 写法）；升级属二期决策，需 PM + BE-C 评审。
- RAG 链路（PDF 解析→切片→向量化→ChromaDB 检索→LLM 流式生成）已于 Day2 通过 `backend/scripts/rag_spike.py` 跑通验证。

## 4. API 规范（强约束）

- 统一前缀：`/api/v1/`
- 统一响应体：`{ "code": 200, "data": {}, "message": "success" }`
- 分页 `data` 结构：`{ "items": [], "total": 0, "page": 1, "page_size": 20 }`
- 认证：**所有接口需认证**，例外仅 `/auth/register` 与 `/auth/login`。
- 流式问答：`POST /api/v1/qa/ask` 返回 **SSE** 流。
- 文档：启动后自动生成 Swagger，`http://localhost:8000/docs`。

## 5. 命名规范

- **数据库表**：小写复数（`courses`、`exam_records`）。
- **字段**：下划线分隔（`created_at`、`course_id`）。
- **外键**：`{表单数}_id`（引用 `courses` → `course_id`，引用 `users` → `user_id`）。
- **主键**：`id`，自增，**签名 `BIGINT`**（不用 UNSIGNED）。
- **索引/约束名**：由 `app/core/database.py` 的 naming_convention 自动生成（`ix_*`/`uq_*`/`fk_*`/`pk_*`），**不要手工命名**（复合索引除外，用 `Index("ix_表名_语义", ...)`）。
- **Python**：模块/函数 `snake_case`，类 `PascalCase`。
- **Vue 组件**：文件与组件名 `PascalCase`（`VideoPlayer.vue`）。

## 6. 数据库纪律：ORM 模型是 schema 唯一真源（重要）

- **`backend/app/models/` 的 SQLAlchemy 模型是表结构的唯一真源**；`docs/database-schema.md` 是导出物，两者不一致时以模型为准并回头修文档。
- **禁止手写 DDL、禁止手改线上/共享库表结构**；一切结构变更：改模型 → `alembic revision --autogenerate` → **人工检查生成的迁移**（autogenerate 可能漏索引/误删列）→ `alembic upgrade head`。
- 约束/索引必须在模型里**真实声明**（`UniqueConstraint` / `Index` / `index=True`），不允许只写注释——注释不建索引。
- 验收标准：改完模型 + 迁移后，`alembic check` 必须输出 *No new upgrade operations detected*。
- **迁移文件在 PR 中单独 review**，不与业务逻辑混在同一次 review 焦点里。
- **`down_revision` 冲突由 DBA 统一 rebase**：多人并行产生分叉 head 时，不要各自 merge，交给 DBA 线性化。
- 应用迁移：`alembic upgrade head`；回滚一版：`alembic downgrade -1`。
- 初始迁移为 `6a1c0f34e2a6`（Day2 由 ORM autogenerate 重新生成，废弃旧手写 DDL `0001`）。**若本地库建于 Day2 之前**：删除本地 `mysql_data` 卷后重新 `alembic upgrade head`。

## 7. Git 分支与提交

- 主分支 `main` 受保护，仅通过 PR 合并。
- 功能分支：`feature/{模块}-{描述}`（如 `feature/course-api`）；修复：`fix/{问题描述}`。
- 每日流程：拉最新 → 功能分支开发 → 推送提 PR → Code Review → 合并。
- 提交信息遵循 **Conventional Commits**：`feat(scope): 描述` / `fix(scope): 描述` / `docs`、`chore`、`refactor`、`test` 等。
  - 例：`feat(course): 实现课程列表分页搜索接口`
- PR：标题遵循提交规范，正文含变更内容 + 测试情况；至少 1 人 review，检查规范/安全/性能/API 一致性。

## 8. 团队分工与十日施工计划

### 8.1 角色与职责

| 角色 | 负责模块 | 职责要点 |
|------|---------|---------|
| **PM** | 统筹/合并 | 需求裁剪、PR 终审合并、每日 17:00 合并节点、风险跟踪（LLM key/大文件/联调阻塞） |
| **FE** | M5/M17/M18/M19 全部前端 | 认证骨架（axios+CSRF+401重放）、路由守卫、课程/播放/答疑/考试/统计页面、SSE 渲染、ECharts |
| **BE-A** | M0/M1/M3/M4/M7 | 项目脚手架、认证/JWT/CSRF、分类/课程/章节 CRUD、课件上传、视频 HTTP Range 流 |
| **BE-B** | M6/M8/M9/M20 | 选课、学习进度/断点/日历、笔记/收藏、学习分析聚合接口 |
| **BE-C** | M10/M11/M12/M13/M14/M15/M16 | 知识点/题库、考试/组卷/自动批改、错题本、**RAG 链路**、知识库构建、SSE 流式问答、AI 学习助手 Agent |
| **DBA/运维** | M2 + 基础设施 | 18 表模型与迁移线性化、Docker Compose、迁移 rebase、部署交付、数据库性能 |

### 8.2 十日里程碑（每日 17:00 为合并节点）

| 日 | 主题 | 完成标准 |
|----|------|---------|
| Day 1 | 地基 | 脚手架 + 认证闭环 + FE 骨架合入 main ✅ |
| Day 2 | 模型基线 | 18 表 ORM 模型 + 初始迁移合入；RAG spike 跑通拿到结论 ✅ |
| Day 3 | 课程域 | 分类/课程/章节 CRUD、知识点/题库 CRUD、Schema 协议对齐；**冻结模型表结构**（此后改动需 DBA 评审） |
| Day 4 | 课件与播放 | 课件上传、视频 Range 流、播放页；DBA rebase 迁移分叉 |
| Day 5 | 选课与学习 | 选课、进度/断点、组卷/批改；中期里程碑：学生能看视频 |
| Day 6 | 学习闭环 | 笔记/收藏、错题本、知识库构建（BackgroundTasks）、播放进度上报 |
| Day 7 | AI 域 | RAG 正式问答 + SSE 流式；qa_history 落库；SSE 渲染联调 |
| Day 8 | Agent 与统计 | AI 学习助手 Agent、学习分析接口 + ECharts、全链路自测 |
| Day 9 | 联调冻结 | 只修 bug 不加功能；跨模块联调、回归测试 |
| Day 10 | 部署交付 | Docker Compose 全栈部署、README/文档终审、release PR + tag |

### 8.3 模块交接标准（每个 PR 必走）

1. 功能分支开发，自测通过（后端 pytest / 前端 build）；
2. `black + flake8` / `npm run lint` 通过；
3. 涉及表结构：迁移文件单独列出，`alembic check` 零输出；
4. PR 描述含：变更内容、测试情况、影响面；
5. 至少 1 人 review（跨模块接口变更需对接人 review）；
6. PM 合并；合并后在群里同步（若含迁移，提醒全员 `alembic upgrade head`）。

## 9. 常用命令

```bash
# 基础设施(数据库/缓存/向量库)
docker compose up -d mysql redis chromadb
docker compose ps
docker compose logs -f mysql

# 后端(在 backend/ 下)
uvicorn app.main:app --reload --port 8000
alembic revision --autogenerate -m "描述"
alembic upgrade head
alembic check              # 模型与库结构一致性验收(应零输出)

# 前端(在 frontend/ 下)
npm install
npm run dev        # 默认 5173
npm run build

# 代码质量
black . && flake8          # 后端
npm run lint               # 前端
```

## 10. 给 Claude Code 的工作约定

- **动手前先读**本文件与对应分层的 `CLAUDE.md`；分层文件与本文件冲突时，以本文件的「关键决策 / API 规范」为准。
- **对照 8.1 分工确认当前任务归属**：不要替其他角色实现其负责模块（如 BE-B 的任务不要顺手做掉 BE-C 的 RAG），跨模块接口先对齐协议再动手。
- **不创建真实 `.env`**，只维护 `.env.example`；不写入任何真实密钥/口令。
- 新增数据表/字段：先改 SQLAlchemy 模型，再生成 Alembic 迁移，**不要手写 DDL 或直接改库**（详见第 6 节纪律）。
- 认证/CSRF/SSE 相关改动，先对照 `docs/decisions/auth.md`，不要退回 Bearer header 方案。
- RAG/向量库相关改动，**不得变更 chromadb/langchain 版本**（决策 4）；参考 `backend/scripts/rag_spike.py` 的已验证链路写法。
- 遵守 API 统一响应体与分页结构；新增接口默认需认证。
- 涉及第三方外发、部署、删除文件等不可逆动作，**先与 PM 确认**再执行。
- 提交走 Conventional Commits；未获明确许可**不要 push**。
