# 在线教育学习平台（Online Learning Platform）

综合性在线教育学习平台：**课程管理、在线学习、智能答疑（RAG）、AI 学习助手、考试测评、学习数据分析**，通过 RAG 与 Agent 技术实现个性化学习。前后端分离，Docker Compose 编排。

- 仓库：https://github.com/MoHui9s/online_learning_platform.git
- 开发周期：10 个工作日　团队：6 人（PM×1、FE×1、BE-A/B/C×3、DBA/运维×1）
- 施工规范见根目录 [`CLAUDE.md`](./CLAUDE.md)；认证决策见 [`docs/decisions/auth.md`](./docs/decisions/auth.md)；数据表设计见 [`docs/database-schema.md`](./docs/database-schema.md)。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3.4+、Vite 5、Element Plus 2.6+、Pinia、Vue Router、Axios、video.js、ECharts |
| 后端 | Python 3.11+、FastAPI 0.110+、SQLAlchemy 2.0、Alembic、Pydantic v2、python-jose、passlib[bcrypt] |
| AI | LangChain 0.2.16、ChromaDB **0.5.3**（客户端与镜像同版本钉死）、OpenAI 兼容接口（可切 Ollama） |
| 数据 | MySQL 8.0、Redis 7.0、ChromaDB（持久化） |
| 部署 | Docker 24+、Docker Compose 2.20+ |

## 关键决策（务必遵守）

1. **认证**：JWT 存 HttpOnly Cookie（access + refresh）+ CSRF 双提交 token。前端不加 `Authorization` header，写操作带 `X-CSRF-Token`；SSE 走原生 `EventSource` 靠 cookie 鉴权。
2. **异步**：MVP 用 FastAPI `BackgroundTasks`，不引入 Celery（二期）。
3. **视频**：MVP 用 HTTP Range 字节流（video.js 支持断点续播/倍速），不做 HLS 转码（二期）。
4. **RAG 版本钉定**：chromadb 客户端与 Docker 镜像统一 **0.5.3**、langchain 全家 0.2.x（0.5.4/0.5.5 被 langchain-chroma 拉黑，勿升级；详见根 `CLAUDE.md` 决策 4）。

## 目录结构

```
online_learning_platform/
├── CLAUDE.md                 # 全员施工规范(总纲)
├── docker-compose.yml        # 本地基础设施(mysql/redis/chromadb)
├── README.md
├── docs/
│   ├── decisions/auth.md     # 认证方案决策
│   └── database-schema.md    # 数据表设计 + ER 图
├── backend/                  # FastAPI 后端
│   ├── CLAUDE.md
│   ├── app/{api,core,models,schemas,services,utils}
│   ├── alembic/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
└── frontend/                 # Vue 3 前端
    ├── CLAUDE.md
    ├── src/{api,components,pages,router,store,composables,utils}
    ├── vite.config.js
    ├── Dockerfile
    └── .env.example
```

## 本地一键启动

### 前置

Docker 24+ / Docker Compose 2.20+、Python 3.11+、Node.js 18+。

### 步骤

```bash
# 1. 克隆
git clone https://github.com/MoHui9s/online_learning_platform.git
cd online_learning_platform

# 2. 复制环境变量模板并填值(切勿提交真实 .env)
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
#   后端 .env: 至少设置 SECRET_KEY / DB_PASSWORD / LLM_API_KEY
#   生成密钥: openssl rand -hex 32

# 3. 起基础设施(数据库/缓存/向量库)
docker compose up -d mysql redis chromadb
docker compose ps        # 等待 healthy

# 4. 后端(新终端, 在 backend/ 下)
cd backend
# 方式 A(推荐): conda 虚拟环境
conda create -y -n edu_platform python=3.11
conda activate edu_platform
# 方式 B: venv
#   python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head          # 初始化/迁移表结构(需 MySQL 已就绪)
uvicorn app.main:app --reload --port 8000

# 5. 前端(新终端, 在 frontend/ 下)
cd frontend
npm install
npm run dev                   # 默认 http://localhost:5173

# 6. 访问
#   前端:   http://localhost:5173
#   API 文档: http://localhost:8000/docs
```

> 说明：ChromaDB 容器内监听 8000，宿主映射到 **8001**，把宿主 8000 留给后端 uvicorn。后端连接 Chroma 时用 `http://localhost:8001`。MySQL 宿主端口为 **3307**（规避本机 3306 占用）。
>
> ⚠️ **本地库建于 Day2 之前的成员**：初始迁移已重写为 `6a1c0f34e2a6`（ORM autogenerate，废弃旧手写 DDL `0001`），需重建本地库：
> `docker compose down mysql && docker volume rm online_learning_platform_mysql_data && docker compose up -d mysql && alembic upgrade head`

## 常用命令

```bash
# 基础设施
docker compose up -d mysql redis chromadb
docker compose logs -f mysql
docker compose down                 # 停止(保留卷/数据)

# 后端
uvicorn app.main:app --reload --port 8000
alembic revision --autogenerate -m "描述"
alembic upgrade head
alembic check      # 模型与库一致性验收(应零输出)
black . && flake8
pytest

# 前端
npm run dev
npm run build
npm run lint
```

## API 规范

- 统一前缀 `/api/v1/`；统一响应体 `{ "code": 200, "data": {}, "message": "success" }`。
- 分页 `data`：`{ "items": [], "total": 0, "page": 1, "page_size": 20 }`。
- 除 `/auth/register`、`/auth/login` 外所有接口需认证。
- Swagger：`http://localhost:8000/docs`。

## 当前进度（截至 Day2）

### Day1 骨架（已合入 main）

- **后端**：认证接口 `/api/v1/auth/{register,login,refresh,logout,me}` + `/health`；JWT 存 HttpOnly Cookie + CSRF 双提交中间件；统一响应体与异常处理。
- **前端**：登录 / 注册 / 首页；Axios 全局封装（`withCredentials` + CSRF 拦截器 + 401 自动 refresh 重放）；Pinia 用户 store；路由登录守卫。
- **验证**：后端认证闭环通过 TestClient 冒烟测试；前端 `npm run build` 通过。

### Day2 模型基线与 RAG 验证（代码就绪，待提 PR 合并）

- **数据库（M2）**：18 张业务表 SQLAlchemy 模型全部落定，**schema 真源反转为 ORM 模型**——统一签名 `BIGINT` 主键、真实 `UniqueConstraint`/`Index` 声明、`app/core/database.py` 命名约定（`ix_*`/`uq_*`/`fk_*`/`pk_*`）；初始迁移重写为 `6a1c0f34e2a6`（autogenerate 生成，废弃手写 DDL），`alembic check` 零输出、downgrade/upgrade 往返通过。
- **RAG（M13 spike）**：`backend/scripts/rag_spike.py` 跑通全链路（PDF 解析 → 500/50 切片 → 向量化 → ChromaDB 检索 → LLM 流式回答），验证后已清理测试数据；版本决策落定为 chromadb 全家 0.5.3（决策 4）。
- **基础设施**：MySQL 卷已用 `.env` 密码重建；chroma 容器切至 0.5.3 镜像并通过读写冒烟。

> 其余业务模块（课程/学习/答疑/考试/分析）按十日计划推进，见根 `CLAUDE.md` 第 8 节的分工与里程碑。端到端跑通需先 `docker compose up -d mysql redis chromadb` 并 `alembic upgrade head` 建表。

## 分支与 PR 流程

- 主分支 `main` 受保护，仅经 PR 合并。
- 功能分支 `feature/{模块}-{描述}`，修复 `fix/{描述}`。
- 提交遵循 **Conventional Commits**（`feat(scope): ...` / `fix(scope): ...`）。
- 每日：拉最新 → 分支开发 → 推送提 PR → 至少 1 人 Review → 合并。
- Alembic 迁移文件在 PR 中单独 review；`down_revision` 冲突由 DBA 统一 rebase（详见 `CLAUDE.md`）。
