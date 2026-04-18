#!/usr/bin/env python3
"""从 JUnit XML 与 Cobertura coverage.xml 汇总质量报告（覆盖率、缺陷率、风险）。"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class JunitSummary:
    tests: int
    failures: int
    errors: int
    skipped: int

    @property
    def failed_total(self) -> int:
        return self.failures + self.errors

    @property
    def defect_rate_percent(self) -> float:
        if self.tests <= 0:
            return 0.0
        return round(100.0 * self.failed_total / self.tests, 2)


def parse_junit(path: Path) -> JunitSummary | None:
    if not path.is_file():
        return None
    tree = ET.parse(path)
    root = tree.getroot()
    # pytest junitxml: <testsuite ...> 或 testsuites 包裹
    if root.tag == "testsuites":
        ts = root.find("testsuite")
        if ts is None:
            return None
        el = ts
    else:
        el = root
    return JunitSummary(
        tests=int(el.attrib.get("tests", 0)),
        failures=int(el.attrib.get("failures", 0)),
        errors=int(el.attrib.get("errors", 0)),
        skipped=int(el.attrib.get("skipped", 0)),
    )


def parse_coverage_line_rate(path: Path) -> float | None:
    if not path.is_file():
        return None
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != "coverage":
        return None
    lr = root.attrib.get("line-rate")
    if lr is None:
        return None
    return round(float(lr) * 100.0, 2)


def risk_level(coverage_pct: float | None, junit: JunitSummary | None) -> tuple[str, str]:
    """返回 (等级, 说明)。"""
    failed = junit.failed_total if junit else 0
    cov = coverage_pct if coverage_pct is not None else 0.0
    if failed > 0:
        return "高", "存在失败或错误的用例，发布前需修复。"
    if coverage_pct is None:
        return "中", "未读取到覆盖率数据，请确认已生成 coverage.xml。"
    if cov < 50:
        return "高", "行覆盖率偏低，关键路径可能缺少自动化验证。"
    if cov < 75:
        return "中", "覆盖率尚可，建议对核心业务与边界条件补充测试。"
    return "低", "测试通过且覆盖率良好，回归风险相对可控。"


def write_markdown(
    out_md: Path,
    junit: JunitSummary | None,
    coverage_pct: float | None,
    risk: str,
    risk_detail: str,
) -> None:
    lines = [
        "# 测试质量报告",
        "",
        "## 摘要",
        "",
    ]
    if junit:
        lines.extend(
            [
                f"- **用例总数**: {junit.tests}",
                f"- **失败**: {junit.failures}，**错误**: {junit.errors}，**跳过**: {junit.skipped}",
                f"- **缺陷率**（失败+错误 / 总数）: **{junit.defect_rate_percent}%**",
                "",
            ]
        )
    else:
        lines.append("- **JUnit**: 未找到或未解析 junit.xml\n")

    if coverage_pct is not None:
        lines.append(f"- **行覆盖率（Cobertura）**: **{coverage_pct}%**\n")
    else:
        lines.append("- **覆盖率**: 未读取到 coverage.xml\n")

    lines.extend(
        [
            "## 风险评估",
            "",
            f"- **等级**: **{risk}**",
            f"- **说明**: {risk_detail}",
            "",
        ]
    )
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")


def write_json(
    out_json: Path,
    junit: JunitSummary | None,
    coverage_pct: float | None,
    risk: str,
    risk_detail: str,
) -> None:
    payload = {
        "junit": None
        if not junit
        else {
            "tests": junit.tests,
            "failures": junit.failures,
            "errors": junit.errors,
            "skipped": junit.skipped,
            "defect_rate_percent": junit.defect_rate_percent,
        },
        "line_coverage_percent": coverage_pct,
        "risk": {"level": risk, "detail": risk_detail},
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="生成测试质量 Markdown/JSON 报告")
    p.add_argument("--junit", type=Path, default=Path("tests/reports/junit.xml"))
    p.add_argument("--coverage", type=Path, default=Path("tests/reports/coverage.xml"))
    p.add_argument("--out-md", type=Path, default=Path("tests/reports/quality_report.md"))
    p.add_argument("--out-json", type=Path, default=Path("tests/reports/quality_report.json"))
    args = p.parse_args(argv)

    junit = parse_junit(args.junit)
    cov = parse_coverage_line_rate(args.coverage)
    risk, detail = risk_level(cov, junit)
    write_markdown(args.out_md, junit, cov, risk, detail)
    write_json(args.out_json, junit, cov, risk, detail)
    print(f"Wrote {args.out_md} and {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
