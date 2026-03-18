"""用户：当前用户信息与设置。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id, is_admin
from app.repositories.user_repo import UserRepository
from app.core.security import hash_password
from app.api.schemas.auth import UserOut
from app.api.schemas.user_schemas import UserUpdateIn

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    uid = int(user_id)
    user = await repo.get_by_id(uid)
    if not user:
        raise HTTPException(404, "User not found")
    return UserOut(id=user.id, username=user.username, is_admin=is_admin(uid))


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserUpdateIn,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    uid = int(user_id)
    user = await repo.get_by_id(uid)
    if not user:
        raise HTTPException(404, "User not found")
    if body.username is not None:
        existing = await repo.get_by_username(body.username)
        if existing and existing.id != uid:
            raise HTTPException(400, "Username already taken")
        user.username = body.username
    if body.password is not None:
        user.password_hash = hash_password(body.password)
    await db.flush()
    await db.refresh(user)
    return UserOut(id=user.id, username=user.username, is_admin=is_admin(uid))
