"""测试进程环境：在导入 app 前设置变量（本仓库纯函数测试不启动 Web/DB）。"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "pytest-jwt-secret")
os.environ.setdefault("PINECONE_API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "")
