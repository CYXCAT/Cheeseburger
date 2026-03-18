"""数据库连接与初始化。"""
import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

logger = logging.getLogger(__name__)
from .models import (  # noqa: F401
    Base,
    BillingAccount,
    BillingLedgerEntry,
    ChatConversation,
    ChatMessage,
    Invite,
    KBVersion,
    KbDocument,
    KnowledgeBase,
    LlmUsageEvent,
    User,
)


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


async def _migrate_users_last_login_at(conn):
    """为已有 users 表添加 last_login_at 列（若不存在）。"""
    url = settings.database_url
    if "postgresql" in url:
        await conn.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE")
        )
    else:
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN last_login_at DATETIME"))
        except Exception as e:
            if "duplicate" not in str(e).lower() and "already exists" not in str(e).lower():
                logger.warning("Migration users.last_login_at: %s", e)
                raise


async def _migrate_kb_owner_user_id(conn):
    """为已有 knowledge_bases 表添加 owner_user_id 列（若不存在）。"""
    url = settings.database_url
    if "postgresql" in url:
        await conn.execute(
            text(
                "ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS owner_user_id INTEGER "
                "REFERENCES users(id) ON DELETE CASCADE"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_bases_owner_user_id "
                "ON knowledge_bases (owner_user_id)"
            )
        )
    else:
        try:
            await conn.execute(
                text("ALTER TABLE knowledge_bases ADD COLUMN owner_user_id INTEGER REFERENCES users(id)")
            )
        except Exception as e:
            if "duplicate" not in str(e).lower() and "already exists" not in str(e).lower():
                logger.warning("Migration knowledge_bases.owner_user_id: %s", e)
                raise


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await _migrate_users_last_login_at(conn)
        await _migrate_kb_owner_user_id(conn)
