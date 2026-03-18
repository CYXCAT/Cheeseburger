"""LLM 用量事件仓储。"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import LlmUsageEvent


class UsageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(
        self,
        *,
        user_id: int,
        kb_id: int | None,
        conversation_id: int | None,
        model: str,
        request_type: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: int,
    ) -> LlmUsageEvent:
        e = LlmUsageEvent(
            user_id=user_id,
            kb_id=kb_id,
            conversation_id=conversation_id,
            model=model,
            request_type=request_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )
        self.db.add(e)
        await self.db.flush()
        await self.db.refresh(e)
        return e

    async def sum_tokens_by_day(
        self,
        *,
        user_id: int,
        start: datetime,
        end: datetime,
    ) -> Sequence[tuple[str, int]]:
        # 返回 (YYYY-MM-DD, total_tokens)
        day = func.date(LlmUsageEvent.created_at)
        r = await self.db.execute(
            select(day, func.sum(LlmUsageEvent.total_tokens))
            .where(
                LlmUsageEvent.user_id == user_id,
                LlmUsageEvent.created_at >= start,
                LlmUsageEvent.created_at < end,
            )
            .group_by(day)
            .order_by(day)
        )
        return [(str(d), int(t or 0)) for d, t in r.all()]
