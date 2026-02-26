"""文档解析：从 PDF、URL、纯文本提取纯文字。"""
from .base import BaseParser, ParsedChunk
from .pdf_parser import PDFParser
from .url_parser import URLParser
from .text_parser import TextParser
from .registry import get_parser, parse_document

__all__ = [
    "BaseParser",
    "ParsedChunk",
    "PDFParser",
    "URLParser",
    "TextParser",
    "get_parser",
    "parse_document",
]
