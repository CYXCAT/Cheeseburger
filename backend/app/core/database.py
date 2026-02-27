"""数据库连接与初始化。"""
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings
from .models import Base, User, Invite, KnowledgeBase, KBVersion, KbDocument, ChatConversation, ChatMessage  # noqa: F401


def _get_engine():
    url = settings.database_url
    is_pg = url.strip().startswith("postgresql")
    if is_pg and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Supabase/PgBouncer transaction pool 不支持 prepared statements，必须关掉缓存
    kwargs = {}
    if is_pg:
        kwargs["connect_args"] = {"statement_cache_size": 0}
    return create_async_engine(url, echo=settings.debug, **kwargs)


engine = _get_engine()
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
