#!/usr/bin/env python3
"""
对比 OpenDataLoader（text）与 pdfplumber 解析同一 PDF 的耗时，并将全文写入 test-pdf/out/。

在仓库根目录执行（需已安装 backend 依赖，建议先激活 backend/venv）：

  python test-pdf/compare_parse.py
  python test-pdf/compare_parse.py --pdf test-pdf/other.pdf --runs 3
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.parsers.pdf_text_extract import (  # noqa: E402
    _extract_opendataloader,
    _extract_pdfplumber,
)


def _time_call(fn, *args, **kwargs):
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    return result, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description="对比两种 PDF 文本抽取方式的速度并保存结果")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=REPO_ROOT / "test-pdf" / "test.pdf",
        help="输入 PDF 路径（默认 test-pdf/test.pdf）",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="每种方式重复次数（取统计量；首次含 JVM 冷启动）",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "test-pdf" / "out",
        help="输出目录",
    )
    args = parser.parse_args()

    pdf_path: Path = args.pdf.resolve()
    if not pdf_path.is_file():
        print(f"找不到 PDF: {pdf_path}", file=sys.stderr)
        return 1

    raw = pdf_path.read_bytes()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = max(1, args.runs)
    odl_times: list[float] = []
    pl_times: list[float] = []
    odl_text = None
    pl_text = None

    for i in range(runs):
        odl_text, dt = _time_call(_extract_opendataloader, raw)
        odl_times.append(dt)
        pl_text, dt = _time_call(_extract_pdfplumber, raw)
        pl_times.append(dt)

    def stat(xs: list[float]) -> dict:
        if len(xs) == 1:
            return {"s": xs[0], "min": xs[0], "max": xs[0], "mean": xs[0]}
        return {
            "s": xs[0],
            "min": min(xs),
            "max": max(xs),
            "mean": statistics.mean(xs),
        }

    odl_stat = stat(odl_times)
    pl_stat = stat(pl_times)

    stem = pdf_path.stem
    odl_path = out_dir / f"{stem}_opendataloader.txt"
    pl_path = out_dir / f"{stem}_pdfplumber.txt"

    if odl_text is not None:
        odl_path.write_text(odl_text, encoding="utf-8")
    else:
        odl_path.write_text(
            "[OpenDataLoader 未产出文本：可能未安装 Java、JAR 失败或输出为空]\n",
            encoding="utf-8",
        )

    pl_path.write_text(pl_text or "", encoding="utf-8")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_pdf": str(pdf_path),
        "input_bytes": len(raw),
        "runs_per_method": runs,
        "opendataloader": {
            "seconds": odl_stat,
            "success": odl_text is not None,
            "char_count": len(odl_text) if odl_text else 0,
            "output_file": str(odl_path.relative_to(REPO_ROOT)),
        },
        "pdfplumber": {
            "seconds": pl_stat,
            "char_count": len(pl_text or ""),
            "output_file": str(pl_path.relative_to(REPO_ROOT)),
        },
    }
    report_path = out_dir / f"{stem}_benchmark.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_lines = [
        f"输入: {pdf_path} ({len(raw)} bytes)",
        f"重复次数: {runs}（以下为每种方式的耗时列表）",
        "",
        f"OpenDataLoader: {odl_times} s",
        f"  → 首跑 {odl_stat['s']:.4f}s, min {odl_stat['min']:.4f}s, max {odl_stat['max']:.4f}s, mean {odl_stat['mean']:.4f}s",
        f"  → 字符数: {report['opendataloader']['char_count']}, 输出: {odl_path.name}",
        "",
        f"pdfplumber: {pl_times} s",
        f"  → 首跑 {pl_stat['s']:.4f}s, min {pl_stat['min']:.4f}s, max {pl_stat['max']:.4f}s, mean {pl_stat['mean']:.4f}s",
        f"  → 字符数: {report['pdfplumber']['char_count']}, 输出: {pl_path.name}",
        "",
        f"JSON: {report_path.name}",
    ]
    summary_text = "\n".join(summary_lines) + "\n"
    (out_dir / f"{stem}_benchmark_summary.txt").write_text(summary_text, encoding="utf-8")
    print(summary_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
