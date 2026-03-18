"""Usage API：用量汇总与明细。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.core.database import get_db
from app.core.models import LlmUsageEvent

router = APIRouter()


def _price_cents_per_1k(model: str) -> int:
    return int(settings.model_prices_cents_per_1k.get(model, 0))


def _cost_cents(total_tokens: int, model: str) -> int:
    price = _price_cents_per_1k(model)
    if price <= 0 or total_tokens <= 0:
        return 0
    return (total_tokens * price + 999) // 1000


class UsageDayOut(BaseModel):
    day: str
    total_tokens: int
    cost_cents: int


class UsageModelOut(BaseModel):
    model: str
    total_tokens: int
    cost_cents: int


class UsageSummaryOut(BaseModel):
    from_ts: str
    to_ts: str
    total_tokens: int
    total_cost_cents: int
    by_day: list[UsageDayOut]
    by_model: list[UsageModelOut]


@router.get("/summary", response_model=UsageSummaryOut)
async def summary(
    days: int = 30,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    uid = int(user_id)
    days = min(max(days, 1), 365)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    # 按天聚合 tokens
    day_expr = func.date(LlmUsageEvent.created_at)
    r1 = await db.execute(
        select(day_expr, func.sum(LlmUsageEvent.total_tokens))
        .where(
            LlmUsageEvent.user_id == uid,
            LlmUsageEvent.created_at >= start,
            LlmUsageEvent.created_at < end,
        )
        .group_by(day_expr)
        .order_by(day_expr)
    )
    by_day: list[UsageDayOut] = []
    total_tokens = 0
    total_cost = 0
    # day 维度无法拆 model，只能用“默认模型”估价（更精确的 cost 走 by_model 累加）
    for d, tok in r1.all():
        t = int(tok or 0)
        by_day.append(UsageDayOut(day=str(d), total_tokens=t, cost_cents=0))
        total_tokens += t

    # 按模型聚合 tokens + cost
    r2 = await db.execute(
        select(LlmUsageEvent.model, func.sum(LlmUsageEvent.total_tokens))
        .where(
            LlmUsageEvent.user_id == uid,
            LlmUsageEvent.created_at >= start,
            LlmUsageEvent.created_at < end,
        )
        .group_by(LlmUsageEvent.model)
        .order_by(func.sum(LlmUsageEvent.total_tokens).desc())
    )
    by_model: list[UsageModelOut] = []
    for model, tok in r2.all():
        t = int(tok or 0)
        c = _cost_cents(t, str(model))
        by_model.append(UsageModelOut(model=str(model), total_tokens=t, cost_cents=c))
        total_cost += c

    # 回填 by_day 的 cost：用“按模型总成本 / 总 tokens”的均摊近似（用于图表展示）
    if total_tokens > 0 and total_cost > 0:
        for i, item in enumerate(by_day):
            approx = int(round(item.total_tokens * (total_cost / total_tokens)))
            by_day[i] = UsageDayOut(day=item.day, total_tokens=item.total_tokens, cost_cents=approx)

    return UsageSummaryOut(
        from_ts=start.isoformat(),
        to_ts=end.isoformat(),
        total_tokens=total_tokens,
        total_cost_cents=total_cost,
        by_day=by_day,
        by_model=by_model,
    )


class UsageEventOut(BaseModel):
    id: int
    kb_id: int | None = None
    model: str
    request_type: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_cents: int
    latency_ms: int
    created_at: str


@router.get("/events", response_model=list[UsageEventOut])
async def events(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    uid = int(user_id)
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    r = await db.execute(
        select(LlmUsageEvent)
        .where(LlmUsageEvent.user_id == uid)
        .order_by(LlmUsageEvent.id.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = list(r.scalars().all())
    out: list[UsageEventOut] = []
    for e in rows:
        out.append(
            UsageEventOut(
                id=e.id,
                kb_id=e.kb_id,
                model=e.model,
                request_type=e.request_type,
                prompt_tokens=e.prompt_tokens,
                completion_tokens=e.completion_tokens,
                total_tokens=e.total_tokens,
                cost_cents=_cost_cents(e.total_tokens, e.model),
                latency_ms=e.latency_ms,
                created_at=e.created_at.isoformat(),
            )
        )
    return out

