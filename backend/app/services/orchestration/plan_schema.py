"""Planner 输出校验与规范化。"""
from __future__ import annotations

import json
import re
from typing import Any

from app.api.schemas.llm import PlanStep, PlannerPlan
from app.core.config import settings

_VALID_KINDS = frozenset({"knowledge", "code", "html", "synthesize"})


def _strip_markdown_fence(content: str) -> str:
    content = (content or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", content, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return content


def _extract_balanced_object(s: str) -> str | None:
    """从首个 { 起按 JSON 字符串规则配对花括号，截取完整对象。"""
    s = s.strip()
    start = s.find("{")
    if start < 0:
        return None
    depth = 0
    i = start
    in_str = False
    esc = False
    while i < len(s):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
        i += 1
    return None


def _try_load_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    for candidate in (text, text.replace("'", '"')):
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    # 尾随逗号等常见非标准写法
    fixed = re.sub(r",(\s*[\]}])", r"\1", text)
    if fixed != text:
        try:
            obj = json.loads(fixed)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    return None


def _parse_json_loose(content: str) -> dict[str, Any] | None:
    content = (content or "").strip()
    if not content:
        return None
    stripped = _strip_markdown_fence(content)
    for chunk in (stripped, content):
        obj = _try_load_json(chunk)
        if obj is not None:
            return obj
    balanced = _extract_balanced_object(stripped) or _extract_balanced_object(content)
    if balanced:
        obj = _try_load_json(balanced)
        if obj is not None:
            return obj
    # 首行 / 单引号等兜底
    for raw in (content.split("\n")[0],):
        obj = _try_load_json(raw)
        if obj is not None:
            return obj
    return None


def normalize_plan_dict(data: dict[str, Any], *, daytona_available: bool, max_steps: int | None = None) -> PlannerPlan:
    max_steps = max_steps if max_steps is not None else settings.planner_max_steps
    max_steps = max(1, min(max_steps, 20))
    reasoning = str(data.get("reasoning_summary") or "").strip()
    raw_steps = data.get("steps")
    if not isinstance(raw_steps, list):
        raw_steps = []
    out_steps: list[PlanStep] = []
    for i, item in enumerate(raw_steps):
        if len(out_steps) >= max_steps:
            break
        if not isinstance(item, dict):
            continue
        sid = str(item.get("id") or "").strip() or str(i + 1)
        kind = str(item.get("kind") or "knowledge").strip().lower()
        if kind not in _VALID_KINDS:
            kind = "knowledge"
        if not daytona_available and kind == "code":
            kind = "synthesize"
        goal = str(item.get("goal") or "").strip() or reasoning or "完成用户需求"
        out_steps.append(PlanStep(id=sid, kind=kind, goal=goal))
    if not out_steps:
        out_steps.append(PlanStep(id="1", kind="knowledge", goal="根据对话回答用户问题"))
    return PlannerPlan(reasoning_summary=reasoning, steps=out_steps[:max_steps])


def parse_planner_response(content: str, *, daytona_available: bool) -> PlannerPlan | None:
    data = _parse_json_loose(content)
    if not data:
        return None
    return normalize_plan_dict(data, daytona_available=daytona_available)
