"""知识库、文档上传、搜索的请求/响应模型。"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KBCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: str | None = None


class KBUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=256)
    description: str | None = None


class KBVersionOut(BaseModel):
    id: int
    kb_id: int
    version_number: int
    status: str
    source_type: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class KBOut(BaseModel):
    id: int
    user_id: str
    name: str
    description: str | None
    current_version_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    kb_id: int
    source_id: str
    source_type: str
    chunks_count: int


class DocumentOut(BaseModel):
    id: int
    kb_id: int
    source_id: str
    source_type: str
    chunks_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    search_type: str = Field("semantic", description="semantic | keyword | hybrid")
    top_k: int = Field(10, ge=1, le=50)


class SearchResult(BaseModel):
    id: str | None
    score: float | None
    chunk_text: str | None
    metadata: dict[str, Any] | None


class SearchResponse(BaseModel):
    results: list[SearchResult]
