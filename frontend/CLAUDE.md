# frontend/CLAUDE.md — 前端施工规范（Vue 3）

> 承接根 `CLAUDE.md`。冲突时以根文件的「关键决策 / API 规范」为准。

## 1. 目录结构

```
frontend/
├── src/
│   ├── api/            # 按模块封装的请求(auth/course/learning/qa/exam/stats)
│   ├── components/     # 通用组件(VideoPlayer 等,PascalCase)
│   ├── pages/          # 页面视图(Home/Course/Learning/QA/Exam/Stats)
│   ├── router/         # Vue Router 配置
│   ├── store/          # Pinia,按模块拆分(user/course/...)
│   ├── composables/    # 组合式函数(useXxx)
│   └── utils/          # request(Axios 封装)、sse、格式化等
├── .env.example
├── vite.config.js
└── Dockerfile
```

## 2. 代码规范

- **ESLint + Prettier**，提交前 `npm run lint`。
- **组合式 API 优先**（`<script setup>`）。
- 组件文件与组件名 **PascalCase**；`<style scoped>`。
- Pinia **按模块拆分** store；用户态放 `store/user`。
- UI 统一 **Element Plus**；复杂组件（视频播放器）做成通用组件供复用。

## 3. 请求层（对齐决策 1 — Cookie + CSRF）

- Axios 全局实例：`baseURL = import.meta.env.VITE_API_BASE_URL`，**`withCredentials: true`**（让浏览器带 cookie）。
- **不要手动设置 `Authorization` header** —— 鉴权靠 HttpOnly cookie 自动携带。
- **请求拦截器**：对 `POST/PUT/DELETE/PATCH`，从可读的 `csrf_token` cookie 取值写入 `X-CSRF-Token` header。
- **响应拦截器**：
  - 统一解包 `{ code, data, message }`，`code !== 200` 走错误提示。
  - 收到 401 时，先尝试调 `/auth/refresh`，成功则重放原请求；失败跳登录。
- 分页统一按 `{ items, total, page, page_size }` 处理。

## 4. SSE 流式问答（对齐决策 1）

- 用原生 **`EventSource`** 连 `/api/v1/qa/ask` 相关流式端点，依赖 cookie 自动鉴权。
- `EventSource` **无法设自定义 header**（正因如此才选 cookie 方案）；如需传参用 query string 或先 POST 建会话再用 GET 流式拉取（与后端约定）。
- 逐段渲染回答，处理 `onmessage`/`onerror`，组件卸载时 `close()`。

## 5. 视频播放（对齐决策 3 — Range 流）

- **video.js** 直连后端视频 URL，浏览器自动发 Range 请求实现断点续播/倍速。
- **MVP 不接 HLS**；video.js 用普通 `video/mp4` source 即可。
- 播放进度定时上报 `learning/progress`。

## 6. 公共基础设施与节奏（FE×1）

- 路由配置、Axios 封装（`utils/request.js`）、全局布局、Pinia 用户 store 为公共地基，**已于 Day1 搭好并合入 main**——业务页面直接复用，不要另起炉灶。
- 复杂通用组件（如 `VideoPlayer`）做成通用组件，多页面复用。
- 页面开发节奏对齐根 CLAUDE.md 第 8.2 节：Day3-4 课程/播放页（M17）→ Day5-7 答疑 SSE 页 → Day8 考试/统计页（M18/M19）。
- 与后端联调前先按 Swagger（`/docs`）对齐接口协议；mock 数据结构必须与统一响应体/分页结构一致。

## 7. 环境变量

- 仅维护 `.env.example`；本地复制为 `.env` 填值，**不提交真实 `.env`**。
- `VITE_API_BASE_URL=http://localhost:8000/api/v1`。

## 8. 常用命令

```bash
npm install
npm run dev      # 默认 5173
npm run build
npm run lint
```
