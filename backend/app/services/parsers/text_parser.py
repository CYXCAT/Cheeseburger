"""纯文本解析：按段落或固定长度分块。"""
from .base import BaseParser, ParsedChunk


class TextParser(BaseParser):
    source_type = "text"
    chunk_size = 500
    chunk_overlap = 50

    def _chunk_text(self, text: str, source_id: str) -> list[ParsedChunk]:
        if not text or not text.strip():
            return []
        chunks: list[ParsedChunk] = []
        start = 0
        idx = 0
        text = text.replace("\r\n", "\n").strip()
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                for sep in ("\n\n", "\n", " "):
                    pos = text.rfind(sep, start, end + 1)
                    if pos > start:
                        end = pos + len(sep)
                        break
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    ParsedChunk(
                        text=chunk_text,
                        source_type=self.source_type,
                        source_id=source_id,
                        chunk_index=idx,
                        metadata={"char_start": start, "char_end": end},
                    )
                )
                idx += 1
            start = end
        return chunks

    def parse(self, raw: bytes | str, source_id: str) -> list[ParsedChunk]:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        return self._chunk_text(raw.strip(), source_id)
