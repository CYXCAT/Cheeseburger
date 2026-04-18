"""PDF 解析：提取纯文本并分块。"""
from .base import BaseParser, ParsedChunk
from .pdf_text_extract import extract_pdf_plain_text


class PDFParser(BaseParser):
    source_type = "pdf"
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
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        text = extract_pdf_plain_text(raw)
        return self._chunk_text(text, source_id)
