"""plan_schema.parse_planner_response：宽松 JSON 与规范化。"""
from __future__ import annotations

import pytest

from app.services.orchestration.plan_schema import parse_planner_response


@pytest.mark.unit
def test_parse_from_markdown_json_fence():
    content = """Here is the plan:
```json
{
  "reasoning_summary": "because",
  "steps": [{"id": "1", "kind": "knowledge", "goal": "answer"}]
}
```
"""
    plan = parse_planner_response(content, daytona_available=True)
    assert plan is not None
    assert plan.reasoning_summary == "because"
    assert len(plan.steps) == 1
    assert plan.steps[0].kind == "knowledge"


@pytest.mark.unit
def test_parse_trailing_comma_in_json():
    content = """
{
  "reasoning_summary": "",
  "steps": [{"id": "1", "kind": "knowledge", "goal": "g"},],
}
"""
    plan = parse_planner_response(content, daytona_available=True)
    assert plan is not None
    assert len(plan.steps) == 1
    assert plan.steps[0].goal == "g"


@pytest.mark.unit
def test_parse_balanced_object_with_noise_prefix():
    content = 'noise prefix {"reasoning_summary": "", "steps": []} trailing'
    plan = parse_planner_response(content, daytona_available=True)
    assert plan is not None
    assert len(plan.steps) == 1
    assert plan.steps[0].kind == "knowledge"


@pytest.mark.unit
def test_parse_code_becomes_synthesize_when_no_daytona():
    content = '{"reasoning_summary": "", "steps": [{"id": "1", "kind": "code", "goal": "run"}]}'
    plan = parse_planner_response(content, daytona_available=False)
    assert plan is not None
    assert plan.steps[0].kind == "synthesize"
