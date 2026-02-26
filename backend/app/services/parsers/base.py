"""解析器基类与通用数据结构。"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ParsedChunk:
    """单段文本块，用于向量化。"""
    text: str
    source_type: str  # pdf | url | text
    source_id: str   # 文档级 id（如 file 名、url、text 的 id）
    chunk_index: int
    metadata: dict | None = None

    def to_record(self, record_id: str) -> dict:
        """转为 Pinecone upsert 所需格式（field_map 使用 chunk_text）。"""
        meta = dict(self.metadata or {})
        meta["source_type"] = self.source_type
        meta["source_id"] = self.source_id
        meta["chunk_index"] = self.chunk_index
        return {
            "_id": record_id,
            "chunk_text": self.text,
            **meta,
        }


class BaseParser(ABC):
    source_type: str = ""

    @abstractmethod
    def parse(self, raw: bytes | str, source_id: str) -> list[ParsedChunk]:
        """解析输入，返回文本块列表。"""
        pass
