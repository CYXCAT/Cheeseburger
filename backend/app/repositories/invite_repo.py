"""邀请链接仓储：FOR UPDATE 锁行，校验并递增 used_count。"""
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Invite

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class InviteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_token_for_update(self, token: str) -> Invite | None:
        r = await self.db.execute(
            select(Invite).where(Invite.token == token).with_for_update()
        )
        return r.scalar_one_or_none()

    def increment_used(self, invite: Invite) -> None:
        invite.used_count += 1

    def increment_failed(self, invite: Invite) -> None:
        invite.failed_attempts += 1
        invite.last_failed_at = datetime.now(timezone.utc)

    def is_lockout(self, invite: Invite) -> bool:
        if invite.failed_attempts < MAX_FAILED_ATTEMPTS:
            return False
        if not invite.last_failed_at:
            return False
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_MINUTES)
        return invite.last_failed_at > cutoff
