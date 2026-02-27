"""对话历史 REST：按知识库列出/创建/获取/删除会话，获取/追加消息。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.repositories import KBRepository, ChatRepository
from app.api.schemas.chat_history import (
    ConversationCreate,
    ConversationOut,
    MessageOut,
    AppendMessagesBody,
)

router = APIRouter()


async def _get_kb_or_404(kb_id: int, user_id: str, db: AsyncSession):
    repo = KBRepository(db)
    kb = await repo.get_kb(kb_id, user_id)
    if not kb:
        raise HTTPException(404, "Knowledge base not found")
    return kb


@router.get("/{kb_id}/chat/conversations", response_model=list[ConversationOut])
async def list_conversations(
    kb_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    repo = ChatRepository(db)
    convs = await repo.list_conversations(kb_id, user_id)
    return [
        ConversationOut(
            id=c.id,
            kb_id=c.kb_id,
            title=c.title,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in convs
    ]


@router.post("/{kb_id}/chat/conversations", response_model=ConversationOut)
async def create_conversation(
    kb_id: int,
    body: ConversationCreate | None = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    repo = ChatRepository(db)
    title = body.title if body else None
    conv = await repo.create_conversation(kb_id, user_id, title=title)
    return ConversationOut(
        id=conv.id,
        kb_id=conv.kb_id,
        title=conv.title,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.get("/{kb_id}/chat/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(
    kb_id: int,
    conversation_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    repo = ChatRepository(db)
    msgs = await repo.get_messages(conversation_id, kb_id, user_id)
    return [MessageOut(**m) for m in msgs]


@router.post("/{kb_id}/chat/conversations/{conversation_id}/messages")
async def append_messages(
    kb_id: int,
    conversation_id: int,
    body: AppendMessagesBody,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    repo = ChatRepository(db)
    ok = await repo.append_messages(
        conversation_id,
        kb_id,
        user_id,
        [m.model_dump() for m in body.messages],
    )
    if not ok:
        raise HTTPException(404, "Conversation not found")
    return {"ok": True}


@router.delete("/{kb_id}/chat/conversations/{conversation_id}")
async def delete_conversation(
    kb_id: int,
    conversation_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    repo = ChatRepository(db)
    ok = await repo.delete_conversation(conversation_id, kb_id, user_id)
    if not ok:
        raise HTTPException(404, "Conversation not found")
    return {"ok": True}
