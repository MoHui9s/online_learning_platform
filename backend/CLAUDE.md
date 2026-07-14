# backend/CLAUDE.md — 后端施工规范（FastAPI）

> 承接根 `CLAUDE.md`。冲突时以根文件的「关键决策 / API 规范」为准。

## 1. 目录结构

```
backend/
├── app/
│   ├── main.py            # FastAPI 入口、路由挂载、中间件(CORS/CSRF)、异常处理
│   ├── api/v1/            # 路由: auth / courses / learning / qa / exam / stats
│   ├── core/             # config(pydantic-settings)、security(JWT/密码/CSRF)、db(引擎/session)、redis
│   ├── models/           # SQLAlchemy 2.0 数据模型(声明式)
│   ├── schemas/          # Pydantic v2 请求/响应模型
│   ├── services/         # 业务逻辑(含 rag_service、agent_service)
│   └── utils/            # 文件上传、视频 Range 流工具、SSE 封装
├── alembic/              # 数据库迁移
├── tests/
├── requirements.txt
├── Dockerfile
└── .env.example
```

## 2. 代码规范

- 遵循 PEP 8；**Black 格式化（行宽 120）**、Flake8 检查。
- 全量**类型注解** + 函数文档字符串。
- SQLAlchemy 2.0 风格：`Mapped[]` / `mapped_column()`；用 `select()` 而非 legacy Query。
- Pydantic **v2**：`model_config = ConfigDict(from_attributes=True)`，不要用 v1 的 `orm_mode`。
- 配置读取统一走 `app/core/config.py`（pydantic-settings 从环境变量加载），**不在业务代码里直接读 `os.environ`**。

## 3. API 约定落地

- 所有路由挂在 `/api/v1/` 下，`APIRouter(prefix=...)` 分模块。
- **统一响应体**：用统一封装（如 `success(data)` / 分页 `paginate(items, total, page, page_size)`）返回 `{code, data, message}`。
- **统一异常处理**：注册全局 exception handler，把校验/业务/未捕获错误也包成统一响应体（`code` 非 200）。
- **认证依赖**：写一个 `get_current_user` 依赖，从 **cookie** 读取 access_token 校验；除 `/auth/register`、`/auth/login` 外所有路由挂该依赖。
- Swagger 自动生成，`/docs`。

## 4. 认证 / CSRF / SSE 实现要点（对齐决策 1）

- 登录成功：设置 `access_token`、`refresh_token` 两个 **HttpOnly** cookie + 一个**可读**的 `csrf_token` cookie。
  - cookie 属性由 env 控制：`HttpOnly=True`、`Secure=COOKIE_SECURE`、`SameSite=COOKIE_SAMESITE`。
- **CSRF 双提交中间件**：对 POST/PUT/DELETE/PATCH 校验 `X-CSRF-Token` header == `csrf_token` cookie，不匹配返回 403。
  - GET/HEAD/OPTIONS 及 `/auth/login`、`/auth/register` 豁免 CSRF。
- `/auth/refresh`：校验 refresh cookie，签发新 access cookie。
- `/auth/logout`：清空全部 auth cookie。
- **SSE**（`qa/ask`）：`media_type="text/event-stream"`，由 `get_current_user` 从 cookie 鉴权；**不要**要求 Authorization header。
- JWT：`python-jose`，算法/过期取自 env；密码 `passlib[bcrypt]`。

## 5. 异步与视频（对齐决策 2 / 3）

- 后台任务用 **FastAPI `BackgroundTasks`**（知识库构建、文档解析等），**不引入 Celery**。
- 视频播放走 **HTTP Range**：解析 `Range` header，返回 `206 Partial Content` + `Content-Range`/`Accept-Ranges`，配合 video.js。**不做 HLS**。

## 6. 数据库与迁移

- 表名小写复数、字段下划线、外键 `{表单数}_id`、主键自增 `id`（详见根规范）。
- 结构变更：改 `app/models/` → `alembic revision --autogenerate -m "..."` → 人工检查 → `alembic upgrade head`。
- **禁止手改表结构**；`down_revision` 分叉交 DBA rebase（见根规范第 6 节）。
- 表设计与 ER 图见 `docs/database-schema.md`。

## 7. 常用命令

```bash
uvicorn app.main:app --reload --port 8000
alembic revision --autogenerate -m "描述"
alembic upgrade head
alembic downgrade -1
black . && flake8
pytest
```
