"""用户仓储。"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, username: str, password_hash: str) -> User:
        u = User(username=username, password_hash=password_hash)
        self.db.add(u)
        await self.db.flush()
        await self.db.refresh(u)
        return u

    async def get_by_username(self, username: str) -> User | None:
        r = await self.db.execute(
            select(User).where(User.username == username)
        )
        return r.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        r = await self.db.execute(select(User).where(User.id == user_id))
        return r.scalar_one_or_none()
