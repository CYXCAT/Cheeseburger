"""知识库与版本的数据访问层，可复用。"""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import KnowledgeBase, KBVersion, KbDocument


class KBRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_kb(self, user_id: str, name: str, description: str | None = None) -> KnowledgeBase:
        owner_user_id: int | None = None
        try:
            owner_user_id = int(user_id)
        except (TypeError, ValueError):
            owner_user_id = None
        kb = KnowledgeBase(owner_user_id=owner_user_id, user_id=user_id, name=name, description=description)
        self.db.add(kb)
        await self.db.flush()
        # 创建初始版本
        ver = KBVersion(kb_id=kb.id, version_number=1, status="active", source_type=None)
        self.db.add(ver)
        await self.db.flush()
        kb.current_version_id = ver.id
        await self.db.flush()
        return kb

    async def get_kb(self, kb_id: int, user_id: str | None = None) -> KnowledgeBase | None:
        q = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        if user_id is not None:
            # 优先走新字段 owner_user_id；同时兼容历史字符串字段 user_id
            try:
                uid_int = int(user_id)
            except (TypeError, ValueError):
                uid_int = None
            if uid_int is None:
                q = q.where(KnowledgeBase.user_id == user_id)
            else:
                q = q.where(or_(KnowledgeBase.owner_user_id == uid_int, KnowledgeBase.user_id == user_id))
        r = await self.db.execute(q)
        return r.scalar_one_or_none()

    async def list_kbs(self, user_id: str) -> list[KnowledgeBase]:
        try:
            uid_int = int(user_id)
        except (TypeError, ValueError):
            uid_int = None
        if uid_int is None:
            q = select(KnowledgeBase).where(KnowledgeBase.user_id == user_id)
        else:
            q = select(KnowledgeBase).where(or_(KnowledgeBase.owner_user_id == uid_int, KnowledgeBase.user_id == user_id))
        r = await self.db.execute(q.order_by(KnowledgeBase.id))
        return list(r.scalars().all())

    async def update_kb(
        self, kb_id: int, user_id: str, name: str | None = None, description: str | None = None
    ) -> KnowledgeBase | None:
        kb = await self.get_kb(kb_id, user_id)
        if not kb:
            return None
        if name is not None:
            kb.name = name
        if description is not None:
            kb.description = description
        await self.db.flush()
        return kb

    async def delete_kb(self, kb_id: int, user_id: str) -> bool:
        kb = await self.get_kb(kb_id, user_id)
        if not kb:
            return False
        await self.db.delete(kb)
        await self.db.flush()
        return True

    async def get_version(self, version_id: int, kb_id: int | None = None) -> KBVersion | None:
        q = select(KBVersion).where(KBVersion.id == version_id)
        if kb_id is not None:
            q = q.where(KBVersion.kb_id == kb_id)
        r = await self.db.execute(q)
        return r.scalar_one_or_none()

    async def get_current_version(self, kb_id: int) -> KBVersion | None:
        r = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = r.scalar_one_or_none()
        if not kb or not kb.current_version_id:
            return None
        return await self.get_version(kb.current_version_id, kb_id)

    async def create_version(
        self, kb_id: int, source_type: str | None = None
    ) -> KBVersion | None:
        kb = await self.get_kb(kb_id, user_id=None)
        if not kb:
            return None
        r = await self.db.execute(
            select(KBVersion).where(KBVersion.kb_id == kb_id).order_by(KBVersion.version_number.desc()).limit(1)
        )
        last = r.scalar_one_or_none()
        next_num = (last.version_number + 1) if last else 1
        ver = KBVersion(kb_id=kb_id, version_number=next_num, status="active", source_type=source_type)
        self.db.add(ver)
        await self.db.flush()
        kb.current_version_id = ver.id
        await self.db.flush()
        return ver

    async def list_versions(self, kb_id: int) -> list[KBVersion]:
        r = await self.db.execute(
            select(KBVersion).where(KBVersion.kb_id == kb_id).order_by(KBVersion.version_number.desc())
        )
        return list(r.scalars().all())

    async def add_document(self, kb_id: int, source_id: str, source_type: str, chunks_count: int) -> KbDocument:
        doc = KbDocument(kb_id=kb_id, source_id=source_id, source_type=source_type, chunks_count=chunks_count)
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def list_documents(self, kb_id: int) -> list[KbDocument]:
        r = await self.db.execute(
            select(KbDocument).where(KbDocument.kb_id == kb_id).order_by(KbDocument.created_at.desc())
        )
        return list(r.scalars().all())

    async def delete_document_record(self, kb_id: int, source_id: str) -> bool:
        r = await self.db.execute(
            select(KbDocument).where(KbDocument.kb_id == kb_id, KbDocument.source_id == source_id)
        )
        doc = r.scalar_one_or_none()
        if not doc:
            return False
        await self.db.delete(doc)
        await self.db.flush()
        return True
