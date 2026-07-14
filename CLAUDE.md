# CLAUDE.md — 在线教育学习平台 · 全员施工规范

> 本文件是全团队（含 Claude Code）的施工总纲。**三个关键决策**与 **API 规范**为强约束，任何代码不得违背。
> 子目录另有 `backend/CLAUDE.md`、`frontend/CLAUDE.md` 承接分层细则。

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
| AI | LangChain 0.1+、ChromaDB 0.5+、OpenAI 兼容接口（可切 Ollama） |
| 数据 | MySQL 8.0、Redis 7.0、ChromaDB（持久化） |
| 部署 | Docker 24+、Docker Compose 2.20+ |

## 3. 三个已锁定的关键决策（强约束，勿违背）

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
- **主键**：`id`，自增。
- **Python**：模块/函数 `snake_case`，类 `PascalCase`。
- **Vue 组件**：文件与组件名 `PascalCase`（`VideoPlayer.vue`）。

## 6. Alembic 迁移协作纪律（重要）

- **禁止手改线上/共享库表结构**；一切结构变更走 SQLAlchemy 模型 → `alembic revision --autogenerate` 生成迁移。
- **迁移文件在 PR 中单独 review**，不与业务逻辑混在同一次 review 焦点里。
- **`down_revision` 冲突由 DBA 统一 rebase**：多人并行产生分叉 head 时，不要各自 merge，交给 DBA 线性化。
- 应用迁移：`alembic upgrade head`；回滚一版：`alembic downgrade -1`。
- 生成迁移后**务必人工检查**自动生成的 SQL（autogenerate 可能漏建索引/误删列）。

## 7. Git 分支与提交

- 主分支 `main` 受保护，仅通过 PR 合并。
- 功能分支：`feature/{模块}-{描述}`（如 `feature/course-api`）；修复：`fix/{问题描述}`。
- 每日流程：拉最新 → 功能分支开发 → 推送提 PR → Code Review → 合并。
- 提交信息遵循 **Conventional Commits**：`feat(scope): 描述` / `fix(scope): 描述` / `docs`、`chore`、`refactor`、`test` 等。
  - 例：`feat(course): 实现课程列表分页搜索接口`
- PR：标题遵循提交规范，正文含变更内容 + 测试情况；至少 1 人 review，检查规范/安全/性能/API 一致性。

## 8. 常用命令

```bash
# 基础设施(数据库/缓存/向量库)
docker compose up -d mysql redis chromadb
docker compose ps
docker compose logs -f mysql

# 后端(在 backend/ 下)
uvicorn app.main:app --reload --port 8000
alembic revision --autogenerate -m "描述"
alembic upgrade head

# 前端(在 frontend/ 下)
npm install
npm run dev        # 默认 5173
npm run build

# 代码质量
black . && flake8          # 后端
npm run lint               # 前端
```

## 9. 给 Claude Code 的工作约定

- **动手前先读**本文件与对应分层的 `CLAUDE.md`；分层文件与本文件冲突时，以本文件的「关键决策 / API 规范」为准。
- **不创建真实 `.env`**，只维护 `.env.example`；不写入任何真实密钥/口令。
- 新增数据表/字段：先改 SQLAlchemy 模型，再生成 Alembic 迁移，**不要手写 DDL 或直接改库**。
- 认证/CSRF/SSE 相关改动，先对照 `docs/decisions/auth.md`，不要退回 Bearer header 方案。
- 遵守 API 统一响应体与分页结构；新增接口默认需认证。
- 涉及第三方外发、部署、删除文件等不可逆动作，**先与 PM 确认**再执行。
- 提交走 Conventional Commits；未获明确许可**不要 push**。
