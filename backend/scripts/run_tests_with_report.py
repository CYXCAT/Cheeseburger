#!/usr/bin/env python3
"""运行 pytest（JUnit + Cobertura）并生成质量报告。请在 backend 目录执行：python scripts/run_tests_with_report.py"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _python_for_backend(root: Path) -> Path:
    """优先使用 backend/.venv-test（测试专用虚拟环境），否则退回当前解释器。"""
    candidates = [
        root / ".venv-test" / "bin" / "python",
        root / ".venv-test" / "bin" / "python3",
        root / ".venv-test" / "Scripts" / "python.exe",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return Path(sys.executable)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    py = _python_for_backend(root)
    reports = root / "tests" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    junit = reports / "junit.xml"
    cov_xml = reports / "coverage.xml"
    cov_html = reports / "htmlcov"

    cmd = [
        str(py),
        "-m",
        "pytest",
        str(root / "tests"),
        f"--junitxml={junit}",
        "--cov=app",
        "--cov-report=term-missing",
        f"--cov-report=xml:{cov_xml}",
        f"--cov-report=html:{cov_html}",
    ]
    print("Using Python:", py, flush=True)
    print("Running:", " ".join(cmd), flush=True)
    rc = subprocess.call(cmd, cwd=str(root))
    gen = root / "tests" / "reporting" / "generate_quality_report.py"
    r2 = subprocess.call([str(py), str(gen)], cwd=str(root))
    return rc if rc != 0 else r2


if __name__ == "__main__":
    raise SystemExit(main())
