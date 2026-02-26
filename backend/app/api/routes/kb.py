"""知识库与版本 REST：创建/列表/更新/删除知识库，版本列表。"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories import KBRepository
from app.api.schemas import KBCreate, KBUpdate, KBOut, KBVersionOut

router = APIRouter()


def _user_id(x_user_id: str | None = Header(None, alias="X-User-Id")) -> str:
    if not x_user_id:
        raise HTTPException(401, "Missing X-User-Id header")
    return x_user_id.strip()


@router.post("", response_model=KBOut)
async def create_kb(
    body: KBCreate,
    user_id: str = Depends(_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = KBRepository(db)
    kb = await repo.create_kb(user_id=user_id, name=body.name, description=body.description)
    return kb


@router.get("", response_model=list[KBOut])
async def list_kbs(
    user_id: str = Depends(_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = KBRepository(db)
    return await repo.list_kbs(user_id)


@router.get("/{kb_id}", response_model=KBOut)
async def get_kb(
    kb_id: int,
    user_id: str = Depends(_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = KBRepository(db)
    kb = await repo.get_kb(kb_id, user_id)
    if not kb:
        raise HTTPException(404, "Knowledge base not found")
    return kb


@router.patch("/{kb_id}", response_model=KBOut)
async def update_kb(
    kb_id: int,
    body: KBUpdate,
    user_id: str = Depends(_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = KBRepository(db)
    kb = await repo.update_kb(kb_id, user_id, name=body.name, description=body.description)
    if not kb:
        raise HTTPException(404, "Knowledge base not found")
    return kb


@router.delete("/{kb_id}", status_code=204)
async def delete_kb(
    kb_id: int,
    user_id: str = Depends(_user_id),
    db: AsyncSession = Depends(get_db),
):
    from app.services.pinecone_service import PineconeService
    repo = KBRepository(db)
    if not await repo.get_kb(kb_id, user_id):
        raise HTTPException(404, "Knowledge base not found")
    PineconeService.delete_namespace(kb_id)
    await repo.delete_kb(kb_id, user_id)


@router.get("/{kb_id}/versions", response_model=list[KBVersionOut])
async def list_versions(
    kb_id: int,
    user_id: str = Depends(_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = KBRepository(db)
    if not await repo.get_kb(kb_id, user_id):
        raise HTTPException(404, "Knowledge base not found")
    return await repo.list_versions(kb_id)
