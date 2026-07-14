# 前端镜像 — 多阶段构建，产物由 nginx 托管
# 构建阶段
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 运行阶段
FROM nginx:1.25-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# SPA history 路由回退：所有未命中路径回 index.html（生产可再挂反向代理到后端）
RUN printf 'server {\n\
  listen 80;\n\
  location / {\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    try_files $uri $uri/ /index.html;\n\
  }\n\
}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
