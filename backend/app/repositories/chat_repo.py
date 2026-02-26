"""对话历史的数据访问层。"""
import json
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import ChatConversation, ChatMessage


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self, kb_id: int, user_id: str, title: str | None = None
    ) -> ChatConversation:
        conv = ChatConversation(kb_id=kb_id, user_id=user_id, title=title)
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def list_conversations(
        self, kb_id: int, user_id: str
    ) -> list[ChatConversation]:
        r = await self.db.execute(
            select(ChatConversation)
            .where(
                ChatConversation.kb_id == kb_id,
                ChatConversation.user_id == user_id,
            )
            .order_by(ChatConversation.updated_at.desc())
        )
        return list(r.scalars().all())

    async def get_conversation(
        self, conversation_id: int, kb_id: int, user_id: str
    ) -> ChatConversation | None:
        r = await self.db.execute(
            select(ChatConversation).where(
                ChatConversation.id == conversation_id,
                ChatConversation.kb_id == kb_id,
                ChatConversation.user_id == user_id,
            )
        )
        return r.scalar_one_or_none()

    async def get_messages(
        self, conversation_id: int, kb_id: int, user_id: str
    ) -> list[dict]:
        conv = await self.get_conversation(conversation_id, kb_id, user_id)
        if not conv:
            return []
        r = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.id.asc())
        )
        rows = list(r.scalars().all())
        out = []
        for m in rows:
            item = {"id": str(m.id), "role": m.role, "content": m.content}
            if m.tool_calls_json:
                try:
                    item["tool_calls"] = json.loads(m.tool_calls_json)
                except (json.JSONDecodeError, TypeError):
                    item["tool_calls"] = None
            out.append(item)
        return out

    async def _message_count(self, conversation_id: int) -> int:
        r = await self.db.execute(
            select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        )
        return len(r.scalars().all())

    async def append_messages(
        self,
        conversation_id: int,
        kb_id: int,
        user_id: str,
        messages: list[dict],
    ) -> bool:
        conv = await self.get_conversation(conversation_id, kb_id, user_id)
        if not conv:
            return False
        n_before = await self._message_count(conversation_id)
        for i, m in enumerate(messages):
            role = (m.get("role") or "user").strip() or "user"
            content = (m.get("content") or "").strip()
            tool_calls = m.get("tool_calls")
            tc_json = json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None
            self.db.add(
                ChatMessage(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    tool_calls_json=tc_json,
                )
            )
            if n_before == 0 and i == 0 and role == "user" and content and not conv.title:
                conv.title = (content[:256] if len(content) > 256 else content) or None
            n_before += 1
        conv.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def set_conversation_title(
        self, conversation_id: int, kb_id: int, user_id: str, title: str
    ) -> bool:
        conv = await self.get_conversation(conversation_id, kb_id, user_id)
        if not conv:
            return False
        conv.title = title[:256] if title else None
        await self.db.flush()
        return True

    async def delete_conversation(
        self, conversation_id: int, kb_id: int, user_id: str
    ) -> bool:
        conv = await self.get_conversation(conversation_id, kb_id, user_id)
        if not conv:
            return False
        await self.db.delete(conv)
        await self.db.flush()
        return True
