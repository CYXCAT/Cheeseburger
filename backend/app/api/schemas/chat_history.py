"""对话历史的请求/响应模型。"""
from typing import Any

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationOut(BaseModel):
    id: int
    kb_id: int
    title: str | None
    created_at: str
    updated_at: str


class MessageIn(BaseModel):
    role: str = "user"
    content: str = ""
    tool_calls: list[dict[str, Any]] | None = None


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    tool_calls: list[dict[str, Any]] | None = None


class AppendMessagesBody(BaseModel):
    messages: list[MessageIn] = Field(..., min_length=1)
