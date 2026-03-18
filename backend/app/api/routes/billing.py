"""Billing API：预付费钱包、流水、手工充值（受限）。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, is_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.models import BillingLedgerEntry, LlmUsageEvent
from app.repositories import BillingRepository

router = APIRouter()


class BillingMeOut(BaseModel):
    user_id: int
    currency: str
    balance_cents: int
    last_30d_usage_tokens: int
    last_30d_spent_cents: int


@router.get("/me", response_model=BillingMeOut)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    uid = int(user_id)
    repo = BillingRepository(db)
    acct = await repo.get_or_create_account(uid, currency=settings.billing_currency)

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=30)

    # 近 30 天 tokens（从 usage events 聚合）
    r1 = await db.execute(
        select(func.sum(LlmUsageEvent.total_tokens)).where(
            LlmUsageEvent.user_id == uid,
            LlmUsageEvent.created_at >= start,
            LlmUsageEvent.created_at < now,
        )
    )
    tokens = int((r1.scalar_one_or_none() or 0) or 0)

    # 近 30 天花费（从账本聚合：usage_debit）
    r2 = await db.execute(
        select(func.sum(BillingLedgerEntry.amount_cents)).where(
            BillingLedgerEntry.user_id == uid,
            BillingLedgerEntry.type == "debit",
            BillingLedgerEntry.reason == "usage_debit",
            BillingLedgerEntry.created_at >= start,
            BillingLedgerEntry.created_at < now,
        )
    )
    spent = int((r2.scalar_one_or_none() or 0) or 0)

    return BillingMeOut(
        user_id=uid,
        currency=acct.currency,
        balance_cents=acct.balance_cents,
        last_30d_usage_tokens=tokens,
        last_30d_spent_cents=spent,
    )


class LedgerEntryOut(BaseModel):
    id: int
    type: str
    amount_cents: int
    reason: str
    ref_type: str | None = None
    ref_id: int | None = None
    created_at: str


@router.get("/ledger", response_model=list[LedgerEntryOut])
async def list_ledger(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    uid = int(user_id)
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    r = await db.execute(
        select(BillingLedgerEntry)
        .where(BillingLedgerEntry.user_id == uid)
        .order_by(BillingLedgerEntry.id.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = list(r.scalars().all())
    return [
        LedgerEntryOut(
            id=e.id,
            type=e.type,
            amount_cents=e.amount_cents,
            reason=e.reason,
            ref_type=e.ref_type,
            ref_id=e.ref_id,
            created_at=e.created_at.isoformat(),
        )
        for e in rows
    ]


class TopupIn(BaseModel):
    user_id: int = Field(..., ge=1)
    amount_cents: int = Field(..., ge=1)
    reason: str = Field(default="topup_manual", max_length=64)


class TopupOut(BaseModel):
    ok: bool
    user_id: int
    new_balance_cents: int


@router.post("/topup", response_model=TopupOut)
async def topup(
    body: TopupIn,
    caller_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    caller = int(caller_user_id)
    if not is_admin(caller):
        raise HTTPException(403, "Forbidden")
    repo = BillingRepository(db)
    acct = await repo.credit(
        user_id=body.user_id,
        amount_cents=body.amount_cents,
        reason=body.reason,
        ref_type="manual",
        ref_id=None,
    )
    return TopupOut(ok=True, user_id=body.user_id, new_balance_cents=acct.balance_cents)

