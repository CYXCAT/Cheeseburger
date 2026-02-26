"""网页解析：请求 URL 并提取正文文本后分块。"""
import re
import requests
from bs4 import BeautifulSoup
from .base import BaseParser, ParsedChunk

# 模拟常见浏览器，避免被目标站 403 拒绝
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


class URLParser(BaseParser):
    source_type = "url"
    chunk_size = 500
    chunk_overlap = 50
    timeout = 15

    def _fetch(self, url: str) -> str:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=self.timeout)
        resp.raise_for_status()
        resp.encoding = resp.encoding or "utf-8"
        return resp.text

    def _extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _chunk_text(self, text: str, source_id: str) -> list[ParsedChunk]:
        if not text or not text.strip():
            return []
        chunks: list[ParsedChunk] = []
        start = 0
        idx = 0
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
        if raw.strip().startswith(("http://", "https://")):
            raw = self._fetch(raw.strip())
        html = raw
        text = self._extract_text(html)
        return self._chunk_text(text, source_id)
