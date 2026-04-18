"""plan_schema：对 `normalize_plan_dict` 的纯输入/输出断言（显式 max_steps，不依赖全局 settings）。"""
import pytest

from app.services.orchestration.plan_schema import normalize_plan_dict


@pytest.mark.unit
def test_normalize_code_becomes_synthesize_when_no_daytona():
    data = {
        "reasoning_summary": "",
        "steps": [{"id": "1", "kind": "code", "goal": "run"}],
    }
    plan = normalize_plan_dict(data, daytona_available=False, max_steps=6)
    assert plan.steps[0].kind == "synthesize"


@pytest.mark.unit
def test_normalize_empty_steps_gets_default():
    plan = normalize_plan_dict(
        {"reasoning_summary": "", "steps": []},
        daytona_available=True,
        max_steps=6,
    )
    assert len(plan.steps) == 1
    assert plan.steps[0].kind == "knowledge"


@pytest.mark.unit
def test_normalize_respects_max_steps():
    data = {
        "reasoning_summary": "",
        "steps": [
            {"id": "1", "kind": "knowledge", "goal": "a"},
            {"id": "2", "kind": "knowledge", "goal": "b"},
            {"id": "3", "kind": "knowledge", "goal": "c"},
        ],
    }
    plan = normalize_plan_dict(data, daytona_available=True, max_steps=2)
    assert len(plan.steps) == 2
