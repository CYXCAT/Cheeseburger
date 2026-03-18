"""管理员 API：用户列表（登录时间、请求数、token 用量、余额）、充值。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, is_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.models import BillingAccount, LlmUsageEvent, User

router = APIRouter()


def _require_admin(user_id: str) -> int:
    uid = int(user_id)
    if not is_admin(uid):
        raise HTTPException(403, "Forbidden")
    return uid


class AdminUserRow(BaseModel):
    user_id: int
    username: str
    created_at: str
    last_login_at: str | None
    request_count: int
    total_tokens: int
    balance_cents: int
    currency: str


@router.get("/users", response_model=list[AdminUserRow])
async def list_users(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    _require_admin(user_id)

    # 所有用户 + 余额（左连 billing_accounts）
    r = await db.execute(
        select(User.id, User.username, User.created_at, User.last_login_at, BillingAccount.balance_cents, BillingAccount.currency)
        .outerjoin(BillingAccount, User.id == BillingAccount.user_id)
        .order_by(User.id)
    )
    rows = r.all()

    # 用量聚合：user_id -> (request_count, total_tokens)
    r2 = await db.execute(
        select(LlmUsageEvent.user_id, func.count(LlmUsageEvent.id).label("cnt"), func.coalesce(func.sum(LlmUsageEvent.total_tokens), 0).label("tokens"))
        .group_by(LlmUsageEvent.user_id)
    )
    usage_map = {uid: (int(cnt), int(tok)) for uid, cnt, tok in r2.all()}

    out = []
    for uid, username, created_at, last_login_at, balance_cents, currency in rows:
        cnt, tokens = usage_map.get(uid, (0, 0))
        if balance_cents is None:
            balance_cents = 0
        if currency is None:
            currency = settings.billing_currency
        out.append(
            AdminUserRow(
                user_id=uid,
                username=username,
                created_at=created_at.isoformat() if created_at else "",
                last_login_at=last_login_at.isoformat() if last_login_at else None,
                request_count=cnt,
                total_tokens=tokens,
                balance_cents=balance_cents,
                currency=currency,
            )
        )
    return out
