"""TextParser：纯文本分块（与 chunk_size 及断行启发式一致）。"""
from __future__ import annotations

import pytest

from app.services.parsers.text_parser import TextParser


@pytest.mark.unit
def test_parse_empty_or_whitespace_returns_no_chunks():
    p = TextParser()
    assert p.parse("", "src") == []
    assert p.parse("   \n\t  ", "src") == []


@pytest.mark.unit
def test_parse_short_text_single_chunk():
    p = TextParser()
    chunks = p.parse("hello world", "doc-1")
    assert len(chunks) == 1
    assert chunks[0].text == "hello world"
    assert chunks[0].source_id == "doc-1"
    assert chunks[0].chunk_index == 0
    assert chunks[0].metadata == {"char_start": 0, "char_end": 11}


@pytest.mark.unit
def test_parse_long_without_separators_splits_by_chunk_size():
    p = TextParser()
    body = "a" * 600
    chunks = p.parse(body, "long")
    assert len(chunks) == 2
    assert chunks[0].text == "a" * 500
    assert chunks[1].text == "a" * 100
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1


@pytest.mark.unit
def test_parse_prefers_paragraph_break_near_boundary():
    p = TextParser()
    head = "x" * 400
    tail = "y" * 400
    text = f"{head}\n\n{tail}"
    chunks = p.parse(text, "para")
    assert len(chunks) == 2
    assert "\n\n" not in chunks[0].text
    assert chunks[0].text.endswith("x")
    assert chunks[1].text.startswith("y")
