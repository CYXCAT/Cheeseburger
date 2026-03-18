"""认证：注册、登录。"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import is_admin
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories import UserRepository, InviteRepository
from app.api.schemas.auth import RegisterIn, LoginIn, UserOut

router = APIRouter()


def _user_out(id: int, username: str, admin: bool = False) -> UserOut:
    return UserOut(id=id, username=username, is_admin=admin)


@router.post("/register", response_model=dict)
async def register(
    body: RegisterIn,
    db: AsyncSession = Depends(get_db),
):
    invite_repo = InviteRepository(db)
    user_repo = UserRepository(db)
    # FOR UPDATE 锁行，同一事务内：校验 → 创建用户 → used_count+1
    invite = await invite_repo.get_by_token_for_update(body.invite_token.strip())
    if not invite:
        raise HTTPException(400, "Invalid invite token")
    if invite.used_count >= invite.max_uses:
        raise HTTPException(400, "Invite link has already been used")
    if invite_repo.is_lockout(invite):
        raise HTTPException(400, "Too many failed attempts for this link, try again later")
    try:
        user = await user_repo.create(body.username.strip(), hash_password(body.password))
        user.last_login_at = datetime.now(timezone.utc)
        invite_repo.increment_used(invite)
        await db.flush()
    except IntegrityError:
        invite_repo.increment_failed(invite)
        await db.commit()
        raise HTTPException(400, "Username already registered")
    token = create_access_token(str(user.id))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_out(user.id, user.username, is_admin(user.id)),
    }


@router.post("/login", response_model=dict)
async def login(
    body: LoginIn,
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.get_by_username(body.username)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid username or password")
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()
    token = create_access_token(str(user.id))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_out(user.id, user.username, is_admin(user.id)),
    }
