# 知识库后端 API（FastAPI + uvicorn）
FROM python:3.12-slim

WORKDIR /app

# 系统依赖（如需 PDF/网络解析可保留）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用层缓存
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 数据库与上传文件建议挂载卷；默认 SQLite 写在 /app/data
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# 从 backend 目录启动时，main 在当前目录
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
