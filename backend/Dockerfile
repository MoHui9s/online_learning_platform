# 后端镜像 — FastAPI (Python 3.11-slim)
FROM python:3.11-slim

# 运行期环境
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 系统依赖(bcrypt/一些库编译、curl 供健康检查)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖以利用构建缓存
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 拷贝源码
COPY . .

# 运行时数据目录(与 .env 中 UPLOAD_DIR / CHROMA_PERSIST_DIR 对应)
RUN mkdir -p uploads chroma_data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
