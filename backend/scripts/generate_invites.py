#!/usr/bin/env python3
"""本地生成邀请链接并写入数据库，不暴露 HTTP 接口。用法（在 backend 目录下）：
    python scripts/generate_invites.py [--count 20] [--base-url https://your-app.com]
  需已配置 DATABASE_URL（.env 或环境变量）。"""
import argparse
import asyncio
import sys
from pathlib import Path

# 保证从 backend 目录执行时可找到 app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import secrets

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.models import Invite, Base


def _get_engine():
    url = settings.database_url
    if url.strip().startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    kwargs = {}
    if url.strip().startswith("postgresql"):
        kwargs["connect_args"] = {"statement_cache_size": 0}
    return create_async_engine(url, echo=False, **kwargs)


async def main(count: int, base_url: str) -> None:
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        base = (base_url or settings.invite_base_url or "http://localhost:5173").strip().rstrip("/")
        for i in range(count):
            token = secrets.token_urlsafe(32)
            inv = Invite(token=token, max_uses=1, used_count=0)
            session.add(inv)
            print(f"{base}/register?token={token}")
        await session.commit()
    await engine.dispose()
    print(f"\n# 已生成 {count} 条邀请链接，每条仅可用 1 次", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成邀请链接并写入数据库")
    parser.add_argument("--count", type=int, default=20, help="生成条数，默认 20")
    parser.add_argument("--base-url", type=str, default="", help="注册页 base URL，用于打印完整链接")
    args = parser.parse_args()
    asyncio.run(main(args.count, args.base_url))
