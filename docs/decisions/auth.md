# 决策记录：认证方案 —— JWT + HttpOnly Cookie + CSRF 双提交

- 状态：**已采纳（锁定）**
- 适用：全平台前后端认证
- 关联：根 `CLAUDE.md` 决策 1、`backend/CLAUDE.md` 第 4 节、`frontend/CLAUDE.md` 第 3/4 节

## 1. 背景与目标

平台需要在浏览器端安全地保存登录态，并支持**智能答疑的流式响应（SSE）**。认证方案要同时满足：

1. 防 XSS 窃取 token；
2. 防 CSRF；
3. **与 SSE / `EventSource` 兼容**。

## 2. 决策：为何 Cookie + CSRF 而非 Bearer

**核心约束：浏览器原生 `EventSource` 不支持设置自定义请求头**（无法带 `Authorization: Bearer <token>`）。

- 若用 **Bearer + localStorage**：
  - token 可被任意 JS 读取，**XSS 一旦得手即泄露**；
  - `EventSource` 无法携带 Authorization header，**SSE 鉴权走不通**（只能改用 fetch-stream 等重实现，成本高、体验差）。
- 选择 **HttpOnly Cookie**：
  - token 存于 HttpOnly cookie，**JS 读不到**，XSS 拿不到 token；
  - cookie 由浏览器**自动携带**，`EventSource` 天然带上，**SSE 鉴权直接可用**；
  - 代价是引入 **CSRF 风险** → 用 **双提交 token（Double-Submit Cookie）** 抵消。

结论：**Cookie 承载 JWT（鉴权自动化 + 抗 XSS）+ CSRF 双提交（抗 CSRF）** 是同时满足三项约束的最优解。

## 3. Cookie 设计

| Cookie | HttpOnly | 可被 JS 读 | 用途 |
|--------|----------|-----------|------|
| `access_token`  | ✅ | ❌ | 访问令牌（短期，默认 30 min） |
| `refresh_token` | ✅ | ❌ | 刷新令牌（长期，默认 7 天），仅用于 `/auth/refresh` |
| `csrf_token`    | ❌ | ✅ | CSRF 双提交比对值（非 HttpOnly，供前端读取回填 header） |

通用属性（由后端 env 控制）：

- `HttpOnly`：access/refresh 为 `true`；csrf 为 `false`。
- `Secure`：`COOKIE_SECURE`，本地 http 开发可 `false`，**生产必须 `true`**。
- `SameSite`：`COOKIE_SAMESITE`，同源部署用 `lax`；**跨站前端用 `none`（此时 `Secure` 必须 `true`）**。
- `Path=/`，`Max-Age` 与各自过期时间一致。

## 4. CSRF 双提交实现要点

原理：攻击者能诱导浏览器**自动带上 cookie**，但**无法读取** `csrf_token` cookie 的值，也无法伪造自定义 header。因此比对「header 里的值」与「cookie 里的值」是否一致即可判定合法来源。

- 登录时，后端额外下发一个**非 HttpOnly** 的 `csrf_token` cookie（随机值，可与会话绑定）。
- 前端**请求拦截器**：对 `POST/PUT/DELETE/PATCH`，读取 `csrf_token` cookie 值，写入 `X-CSRF-Token` header。
- 后端**中间件**：对写方法校验 `header(X-CSRF-Token) == cookie(csrf_token)`，不一致返回 `403`。
- 豁免：`GET/HEAD/OPTIONS`（安全方法）、以及 `/auth/login`、`/auth/register`（此时尚无会话）。
- CORS 需 `allow_credentials=true`，且 `allow_origins` 为**精确前端域名**（不能用 `*`）；header 放行 `X-CSRF-Token`。

## 5. access / refresh / logout 流程

```
登录  POST /auth/login
  校验账号密码(bcrypt) → 签发 access + refresh(JWT) → Set-Cookie 三个(access/refresh/csrf)
  → 响应体返回用户信息(不含 token 明文)

访问受保护接口
  浏览器自动带 access_token cookie → 依赖 get_current_user 校验 → 放行
  写操作额外校验 X-CSRF-Token == csrf_token cookie

access 过期(401)
  前端响应拦截器捕获 401 → 调 POST /auth/refresh(自动带 refresh cookie)
    成功 → 后端重签 access(+可选轮换 refresh/csrf) → 重放原请求
    失败 → 清理并跳转登录

登出  POST /auth/logout
  后端清空 access/refresh/csrf 三个 cookie(Set-Cookie 过期) → 前端跳登录
```

## 6. SSE / EventSource 兼容

- 智能答疑 `POST /api/v1/qa/ask`（及相关流式端点）返回 `text/event-stream`。
- 前端用原生 `new EventSource(url, { withCredentials: true })`，**依赖 cookie 自动鉴权**。
- `EventSource` **不能设自定义 header** → 不要求 `Authorization`；如需鉴权即靠 access cookie。
- `EventSource` 只支持 GET；若提问需传较大 body，约定「先 POST 建会话拿 stream_id，再 GET 流式拉取」或用 query 传参（前后端对齐）。
- 跨站场景：cookie 必须 `SameSite=None; Secure`，否则浏览器不带 cookie，SSE 会 401。

## 7. 前端配合方式（要点）

- Axios 实例 `withCredentials: true`；**不手动加 Authorization**。
- 请求拦截器：写方法回填 `X-CSRF-Token`（取自 `csrf_token` cookie）。
- 响应拦截器：401 → 尝试 `/auth/refresh` → 重放/跳登录。
- 详见 `frontend/CLAUDE.md` 第 3、4 节。

## 8. 二期 / 待办

- refresh token 轮换（rotation）与撤销列表（Redis 黑名单）。
- CSRF token 与用户会话强绑定 + 定期轮换。
- 生产环境统一 `Secure=true` + `SameSite` 按部署拓扑最终确认。
