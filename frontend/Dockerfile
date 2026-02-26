# 阶段一：构建前端静态资源
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
# 生产环境由 nginx 代理 /api，前端请求同源，无需写死后端地址
ENV VITE_API_BASE_URL=
RUN npm run build

# 阶段二：用 nginx 提供静态资源并代理 /api
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
