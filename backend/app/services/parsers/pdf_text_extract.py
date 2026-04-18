"""PDF 纯文本抽取：优先 OpenDataLoader（Java），不可用时回退 pdfplumber。"""
from __future__ import annotations

import io
import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import opendataloader_pdf
except ImportError:
    opendataloader_pdf = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def _read_text_outputs(output_dir: Path) -> str:
    parts: list[str] = []
    for path in sorted(output_dir.rglob("*.txt")):
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8", errors="replace").strip())
    return "\n\n".join(p for p in parts if p)


def _extract_opendataloader(raw: bytes) -> str | None:
    """成功返回文本；跳过或失败返回 None（由调用方决定是否回退）。"""
    if opendataloader_pdf is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pdf_path = root / "input.pdf"
        out_dir = root / "out"
        out_dir.mkdir(parents=True)
        pdf_path.write_bytes(raw)
        try:
            opendataloader_pdf.convert(
                input_path=str(pdf_path),
                output_dir=str(out_dir),
                format="text",
                quiet=True,
            )
        except FileNotFoundError:
            logger.warning("opendataloader-pdf: Java 未在 PATH 中，使用 pdfplumber 回退")
            return None
        except subprocess.CalledProcessError as e:
            logger.warning(
                "opendataloader-pdf 失败 (exit=%s)，使用 pdfplumber 回退: %s",
                e.returncode,
                (e.stderr or e.stdout or str(e))[:200],
            )
            return None
        text = _read_text_outputs(out_dir)
        return text if text else None


def _extract_pdfplumber(raw: bytes) -> str:
    if pdfplumber is None:
        raise RuntimeError("需要安装 pdfplumber，或在环境中配置 Java 11+ 以使用 opendataloader-pdf")
    buf = io.BytesIO(raw)
    pages: list[str] = []
    with pdfplumber.open(buf) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\n\n".join(pages)


def extract_pdf_plain_text(raw: bytes) -> str:
    """
    从 PDF 字节得到合并纯文本。
    OpenDataLoader 不可用时使用 pdfplumber；两者皆空则返回空字符串。
    """
    if not raw:
        return ""
    odl = _extract_opendataloader(raw)
    if odl is not None and odl.strip():
        return odl.strip()
    return _extract_pdfplumber(raw).strip()
