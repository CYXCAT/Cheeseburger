"""LLM 对话与工具调用的请求/响应模型。"""
from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="user | assistant | system")
    content: str = ""


class ChatRequest(BaseModel):
    kb_id: int = Field(..., description="知识库 ID，用于工具检索")
    messages: list[ChatMessage] = Field(..., min_length=1)
    stream: bool = False


class CitationChunk(BaseModel):
    """Agent 检索工具返回的片段，用于左侧预览高亮。"""
    chunk_text: str = ""
    source_id: str | None = None
    source_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    message: ChatMessage
    tool_calls: list[dict[str, Any]] | None = None
    citation_chunks: list[CitationChunk] | None = None
