"""预付费钱包与账本仓储。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import BillingAccount, BillingLedgerEntry


class BillingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_account(self, user_id: int, currency: str = "USD") -> BillingAccount:
        r = await self.db.execute(select(BillingAccount).where(BillingAccount.user_id == user_id))
        acct = r.scalar_one_or_none()
        if acct:
            return acct
        acct = BillingAccount(user_id=user_id, balance_cents=0, currency=currency)
        self.db.add(acct)
        await self.db.flush()
        await self.db.refresh(acct)
        return acct

    async def get_account_for_update(self, user_id: int) -> BillingAccount | None:
        r = await self.db.execute(
            select(BillingAccount).where(BillingAccount.user_id == user_id).with_for_update()
        )
        return r.scalar_one_or_none()

    async def append_ledger_entry(
        self,
        *,
        user_id: int,
        entry_type: str,
        amount_cents: int,
        reason: str,
        ref_type: str | None = None,
        ref_id: int | None = None,
    ) -> BillingLedgerEntry:
        e = BillingLedgerEntry(
            user_id=user_id,
            type=entry_type,
            amount_cents=amount_cents,
            reason=reason,
            ref_type=ref_type,
            ref_id=ref_id,
        )
        self.db.add(e)
        await self.db.flush()
        return e

    async def credit(
        self,
        *,
        user_id: int,
        amount_cents: int,
        reason: str,
        ref_type: str | None = None,
        ref_id: int | None = None,
    ) -> BillingAccount:
        acct = await self.get_account_for_update(user_id)
        if not acct:
            acct = await self.get_or_create_account(user_id)
            acct = await self.get_account_for_update(user_id)
        assert acct is not None
        acct.balance_cents += amount_cents
        await self.append_ledger_entry(
            user_id=user_id,
            entry_type="credit",
            amount_cents=amount_cents,
            reason=reason,
            ref_type=ref_type,
            ref_id=ref_id,
        )
        await self.db.flush()
        await self.db.refresh(acct)
        return acct

    async def debit(
        self,
        *,
        user_id: int,
        amount_cents: int,
        reason: str,
        ref_type: str | None = None,
        ref_id: int | None = None,
        require_sufficient_balance: bool = True,
    ) -> BillingAccount:
        acct = await self.get_account_for_update(user_id)
        if not acct:
            acct = await self.get_or_create_account(user_id)
            acct = await self.get_account_for_update(user_id)
        assert acct is not None

        if require_sufficient_balance and acct.balance_cents < amount_cents:
            raise ValueError("INSUFFICIENT_BALANCE")

        acct.balance_cents -= amount_cents
        await self.append_ledger_entry(
            user_id=user_id,
            entry_type="debit",
            amount_cents=amount_cents,
            reason=reason,
            ref_type=ref_type,
            ref_id=ref_id,
        )
        await self.db.flush()
        await self.db.refresh(acct)
        return acct
