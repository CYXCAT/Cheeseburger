"""编排器模块内纯函数（无副作用、不读配置）：输入 → 输出。"""
from __future__ import annotations

from app.api.schemas.llm import ChatMessage, ChatResponse, PlanStep
from app.services.orchestration import orchestrator as orch


def test_to_openai_messages():
    assert orch._to_openai_messages([ChatMessage(role="user", content="a")]) == [
        {"role": "user", "content": "a"}
    ]


def test_should_inject_step_context():
    assert orch._should_inject_step_context(2, "") is True
    assert orch._should_inject_step_context(1, "ctx") is True
    assert orch._should_inject_step_context(1, "") is False


def test_messages_for_step_injects_when_requested():
    sub = orch._messages_for_step(
        [ChatMessage(role="user", content="hi")],
        PlanStep(id="1", kind="knowledge", goal="g"),
        "ctx",
        inject_context=True,
    )
    assert sub[-1].role == "user"
    assert "执行计划" in (sub[-1].content or "")


def test_messages_for_step_no_inject():
    base = [ChatMessage(role="user", content="hi")]
    out = orch._messages_for_step(
        base,
        PlanStep(id="1", kind="knowledge", goal="g"),
        "ctx",
        inject_context=False,
    )
    assert out == base


def test_code_failed():
    assert orch._code_failed(None) is True
    assert orch._code_failed({"exit_code": 1}) is True
    assert orch._code_failed({"exit_code": 0}) is False


def test_merge_preview():
    r = ChatResponse(message=ChatMessage(role="assistant", content="x"), citation_chunks=None)
    c, co, h = orch._merge_preview(r, citations=None, code=None, html=None)
    assert c is None and co is None and h is None


def test_final_intent_mapping():
    assert orch._final_intent(2, 0, "knowledge") == "multi"
    assert orch._final_intent(1, 0, "knowledge") == "kb"
    assert orch._final_intent(1, 0, "code") == "code"
    assert orch._final_intent(1, 0, "html") == "html"
    assert orch._final_intent(1, 0, "synthesize") == "multi"
