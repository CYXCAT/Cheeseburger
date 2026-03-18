"""数据库模型：users、invites、knowledge_bases、kb_versions、billing、usage 等。"""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Invite(Base):
    """邀请链接表：每条链接仅能用 1 次（max_uses=1），used_count 在事务内 +1 防超用。"""
    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    max_uses: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 新字段：统一用 users.id 作为 owner（给 usage/billing 等强一致外键用）
    owner_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    # 兼容字段：历史遗留（字符串），迁移完成后可移除
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_version_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("kb_versions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 不建 versions 反向关系，避免与 current_version_id 双外键歧义；版本列表用 list_versions(kb_id) 查询


class KBVersion(Base):
    __tablename__ = "kb_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kb_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    source_type: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # pdf | url | text，同一库可混合来源
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    knowledge_base: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", foreign_keys=[kb_id])


class KbDocument(Base):
    """知识库内已上传文档的登记表，用于列表与删除。"""
    __tablename__ = "kb_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kb_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    chunks_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ChatConversation(Base):
    """单条对话会话（知识库维度下的“一条历史记录”）。"""
    __tablename__ = "chat_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kb_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ChatMessage(Base):
    """会话中的单条消息。"""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tool_calls_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class LlmUsageEvent(Base):
    """LLM 用量事件：每次模型调用一条（一次对话可能产生多条，如 tool 前/后两次 completion）。"""
    __tablename__ = "llm_usage_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    kb_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="SET NULL"), index=True, nullable=True
    )
    conversation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chat_conversations.id", ondelete="SET NULL"), index=True, nullable=True
    )
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    request_type: Mapped[str] = mapped_column(String(32), nullable=False)  # chat_first | chat_final | etc.
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BillingAccount(Base):
    """预付费钱包账户：每用户一条。"""
    __tablename__ = "billing_accounts"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    balance_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BillingLedgerEntry(Base):
    """账本流水（append-only）。amount_cents 为正数，方向由 type 决定。"""
    __tablename__ = "billing_ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # credit | debit | adjustment
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    ref_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # llm_usage_event | ...
    ref_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
