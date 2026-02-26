"""根据 source_type 选择解析器并执行解析。"""
from .base import ParsedChunk
from .pdf_parser import PDFParser
from .url_parser import URLParser
from .text_parser import TextParser

_PARSERS = {
    "pdf": PDFParser(),
    "url": URLParser(),
    "text": TextParser(),
}


def get_parser(source_type: str):
    t = (source_type or "text").lower()
    if t not in _PARSERS:
        raise ValueError(f"Unsupported source_type: {source_type}")
    return _PARSERS[t]


def parse_document(raw: bytes | str, source_id: str, source_type: str) -> list[ParsedChunk]:
    parser = get_parser(source_type)
    return parser.parse(raw, source_id)
