# 单镜像：前端(nginx 静态) + 后端(uvicorn)，同容器内运行
# 构建：docker build -t doc-app .  或  docker compose up -d（使用下方 compose）

# 阶段一：构建前端
FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
ENV VITE_API_BASE_URL=
RUN npm run build

# 阶段二：运行时（Python + nginx，同镜像内跑后端与前端）
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

# 后端
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# 前端静态
COPY --from=frontend /app/dist /usr/share/nginx/html

# nginx 代理到本机 8000
COPY docker/nginx-single.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
