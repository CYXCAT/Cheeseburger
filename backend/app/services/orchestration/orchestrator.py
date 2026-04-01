"""按 Planner 输出顺序执行步骤，支持代码失败后再规划与步骤异常再规划。"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.api.schemas.llm import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    CitationChunk,
    ExecutionStepTrace,
    PlanStep,
    PlannerPlan,
)
from app.core.config import settings
from app.services.agents import coding_chat, html_chat
from app.services.kb_chat_turn import run_kb_agent_turn
from app.services.orchestration.replanner import run_replanner

if TYPE_CHECKING:
    from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


def _to_openai_messages(messages: list[ChatMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content or ""} for m in messages]


@dataclass
class OrchestrationResult:
    response: ChatResponse
    usage_segments: list[tuple[str, int, int, int]] = field(default_factory=list)


def _should_inject_step_context(steps_len: int, working_context: str) -> bool:
    """多步或已有前置上下文时，为当前步注入子目标与 working_context。"""
    if steps_len > 1:
        return True
    return bool(working_context.strip())


def _messages_for_step(
    base: list[ChatMessage],
    step: PlanStep,
    working_context: str,
    *,
    inject_context: bool,
) -> list[ChatMessage]:
    if not inject_context:
        return list(base)
    inj = (
        f"[执行计划 · 步骤 {step.id} · {step.kind}]\n{step.goal}\n\n"
        f"---\n当前累积上下文（供本步使用）：\n{working_context[:6000]}"
    )
    return list(base) + [ChatMessage(role="user", content=inj)]


def _code_failed(code_result: dict | None) -> bool:
    if not code_result:
        return True
    try:
        return int(code_result.get("exit_code", -1)) != 0
    except (TypeError, ValueError):
        return True


def _merge_preview(
    resp: ChatResponse,
    *,
    citations: list[CitationChunk] | None,
    code: dict | None,
    html: str | None,
) -> tuple[list[CitationChunk] | None, dict | None, str | None]:
    c = list(resp.citation_chunks) if resp.citation_chunks else citations
    co = resp.code_result if resp.code_result is not None else code
    h = resp.html_content if resp.html_content else html
    return c, co, h


async def _run_synthesize(
    client: AsyncOpenAI,
    base_messages: list[ChatMessage],
    working_context: str,
) -> tuple[ChatResponse, tuple[str, int, int, int]]:
    last_user = next((m.content for m in reversed(base_messages) if m.role == "user"), "").strip() or "回答用户问题"
    msgs: list[dict] = [
        {
            "role": "system",
            "content": "你是总结助手。根据「执行上下文」回答用户问题，条理清晰，可适度使用列表。不要编造上下文中不存在的事实。",
        },
        *_to_openai_messages(base_messages[-10:]),
        {
            "role": "user",
            "content": f"用户原始问题（参考）：\n{last_user[:3000]}\n\n执行上下文：\n{working_context[:12000]}",
        },
    ]
    t0 = time.perf_counter()
    final = await client.chat.completions.create(
        model=settings.llm_model,
        messages=msgs,
        max_tokens=settings.billing_max_completion_tokens if settings.billing_enabled else None,
    )
    lat = int((time.perf_counter() - t0) * 1000)
    usage = getattr(final, "usage", None)
    p = int(getattr(usage, "prompt_tokens", 0) or 0)
    c = int(getattr(usage, "completion_tokens", 0) or 0)
    choice = final.choices[0] if final.choices else None
    text = (choice.message.content or "").strip() if choice else "汇总完成。"
    resp = ChatResponse(message=ChatMessage(role="assistant", content=text), intent="multi")
    return resp, ("orchestrator_synthesize", p, c, lat)


def _final_intent(trace_len: int, replan_used: int, first_kind: str | None) -> str:
    if trace_len > 1 or replan_used > 0:
        return "multi"
    if first_kind == "knowledge":
        return "kb"
    if first_kind == "code":
        return "code"
    if first_kind == "html":
        return "html"
    if first_kind == "synthesize":
        return "multi"
    return "kb"


async def _replan_merge(
    client: AsyncOpenAI,
    body: ChatRequest,
    original_plan: PlannerPlan,
    trace: list[ExecutionStepTrace],
    failed_step: PlanStep,
    working_context: str,
    error_summary: str,
    daytona_available: bool,
    replan_used: int,
    step_index: int,
    steps: list[PlanStep],
    usage_segments: list[tuple[str, int, int, int]],
) -> tuple[list[PlanStep], int, bool]:
    """
    调用再规划并合并步骤队列。
    返回 (new_steps, new_replan_used, merged_ok)。merged_ok=False 时应跳过本步或结束。
    """
    if replan_used >= settings.orchestration_max_replan:
        return steps, replan_used, False
    new_replan = replan_used + 1
    new_plan, rp, ct = await run_replanner(
        client,
        body.messages,
        original_plan=original_plan,
        completed_trace=trace,
        failed_step=failed_step,
        error_summary=error_summary[:2000],
        working_context=working_context,
        daytona_available=daytona_available,
    )
    usage_segments.append(("replanner", rp, ct, 0))
    if not new_plan.steps:
        logger.warning("replanner returned empty steps")
        return steps, new_replan, False
    merged = steps[:step_index] + list(new_plan.steps)
    logger.info("replan merged: index=%s new_tail_len=%s", step_index, len(new_plan.steps))
    return merged, new_replan, True


async def run_orchestration(
    client: AsyncOpenAI,
    body: ChatRequest,
    plan: PlannerPlan,
    *,
    daytona_available: bool,
    plan_summary: str,
    kb_usage_events: tuple[str, str] = ("orch_kb_first", "orch_kb_final"),
) -> OrchestrationResult:
    steps: list[PlanStep] = list(plan.steps)
    trace: list[ExecutionStepTrace] = []
    usage_segments: list[tuple[str, int, int, int]] = []
    working_context = ""
    preview_citations: list[CitationChunk] | None = None
    preview_code: dict | None = None
    preview_html: str | None = None
    replan_used = 0
    last_assistant = ""
    last_tool_calls: list[dict] | None = None
    first_kind = steps[0].kind if steps else None

    i = 0
    loop_guard = 0
    max_loops = settings.orchestration_max_loop_iterations

    while i < len(steps):
        loop_guard += 1
        if loop_guard > max_loops:
            logger.error("orchestration exceeded max loop iterations (%s)", max_loops)
            last_assistant = last_assistant or "编排步骤过多，已中止。请简化问题后重试。"
            break

        step = steps[i]
        inject = _should_inject_step_context(len(steps), working_context)
        sub_messages = _messages_for_step(body.messages, step, working_context, inject_context=inject)

        if step.kind == "knowledge":
            trace.append(ExecutionStepTrace(step_id=step.id, kind=step.kind, status="running", summary=""))
            try:
                resp, segs = await run_kb_agent_turn(
                    client,
                    body.kb_id,
                    sub_messages,
                    first_event_type=kb_usage_events[0],
                    final_event_type=kb_usage_events[1],
                )
            except Exception as e:
                logger.exception("knowledge step error: %s", e)
                trace[-1] = ExecutionStepTrace(
                    step_id=step.id,
                    kind=step.kind,
                    status="failed",
                    summary=str(e)[:400],
                )
                merged, ru, ok = await _replan_merge(
                    client,
                    body,
                    plan,
                    trace,
                    step,
                    working_context,
                    str(e),
                    daytona_available,
                    replan_used,
                    i,
                    steps,
                    usage_segments,
                )
                if ok:
                    steps = merged
                    replan_used = ru
                    continue
                working_context += f"\n### 步骤 {step.id}（知识）异常\n{str(e)[:500]}\n"
                i += 1
                continue

            usage_segments.extend(segs)
            summ = (resp.message.content or "")[:800]
            working_context += f"\n### 步骤 {step.id}（知识）\n{summ}\n"
            preview_citations, preview_code, preview_html = _merge_preview(
                resp, citations=preview_citations, code=preview_code, html=preview_html
            )
            last_assistant = resp.message.content or last_assistant
            last_tool_calls = resp.tool_calls
            trace[-1] = ExecutionStepTrace(
                step_id=step.id,
                kind=step.kind,
                status="done",
                summary=summ[:400],
            )
            i += 1
            continue

        if step.kind == "code":
            trace.append(ExecutionStepTrace(step_id=step.id, kind=step.kind, status="running", summary=""))
            if not daytona_available:
                skip_msg = "当前环境未配置代码沙箱，无法执行代码。如需运行脚本请配置 DAYTONA_API_KEY。"
                last_assistant = skip_msg
                trace[-1] = ExecutionStepTrace(
                    step_id=step.id,
                    kind=step.kind,
                    status="skipped",
                    summary="沙箱不可用，跳过代码执行",
                )
                working_context += f"\n### 步骤 {step.id}（代码）\n已跳过：沙箱未配置。\n"
                i += 1
                continue

            try:
                resp, segs = await coding_chat(client, sub_messages)
            except Exception as e:
                logger.exception("code step error: %s", e)
                trace[-1] = ExecutionStepTrace(
                    step_id=step.id,
                    kind=step.kind,
                    status="failed",
                    summary=str(e)[:400],
                )
                merged, ru, ok = await _replan_merge(
                    client,
                    body,
                    plan,
                    trace,
                    step,
                    working_context,
                    str(e),
                    daytona_available,
                    replan_used,
                    i,
                    steps,
                    usage_segments,
                )
                if ok:
                    steps = merged
                    replan_used = ru
                    continue
                working_context += f"\n### 步骤 {step.id}（代码）异常\n{str(e)[:500]}\n"
                i += 1
                continue

            usage_segments.extend(segs)
            preview_citations, preview_code, preview_html = _merge_preview(
                resp, citations=preview_citations, code=preview_code, html=preview_html
            )
            last_assistant = resp.message.content or last_assistant
            last_tool_calls = None
            cr = resp.code_result

            if _code_failed(cr if isinstance(cr, dict) else None) and replan_used < settings.orchestration_max_replan:
                err = ""
                if isinstance(cr, dict):
                    err = f"exit_code={cr.get('exit_code')} result={str(cr.get('result', ''))[:1200]}"
                trace[-1] = ExecutionStepTrace(
                    step_id=step.id,
                    kind=step.kind,
                    status="failed",
                    summary=err[:400] or "代码执行失败",
                )
                merged, ru, ok = await _replan_merge(
                    client,
                    body,
                    plan,
                    trace,
                    step,
                    working_context,
                    err or "unknown",
                    daytona_available,
                    replan_used,
                    i,
                    steps,
                    usage_segments,
                )
                if ok:
                    steps = merged
                    replan_used = ru
                    continue
                summ = (resp.message.content or "")[:800]
                trace[-1] = ExecutionStepTrace(
                    step_id=step.id,
                    kind=step.kind,
                    status="failed",
                    summary=summ[:400],
                )
                working_context += f"\n### 步骤 {step.id}（代码）\n{summ}\n"
                i += 1
                continue

            summ = (resp.message.content or "")[:800]
            if _code_failed(cr if isinstance(cr, dict) else None):
                trace[-1] = ExecutionStepTrace(
                    step_id=step.id,
                    kind=step.kind,
                    status="failed",
                    summary=summ[:400],
                )
            else:
                trace[-1] = ExecutionStepTrace(
                    step_id=step.id,
                    kind=step.kind,
                    status="done",
                    summary=summ[:400],
                )
            working_context += f"\n### 步骤 {step.id}（代码）\n{summ}\n"
            i += 1
            continue

        if step.kind == "html":
            trace.append(ExecutionStepTrace(step_id=step.id, kind=step.kind, status="running", summary=""))
            try:
                t0 = time.perf_counter()
                resp, p_tok, c_tok = await html_chat(client, sub_messages)
                lat = int((time.perf_counter() - t0) * 1000)
            except Exception as e:
                logger.exception("html step error: %s", e)
                trace[-1] = ExecutionStepTrace(
                    step_id=step.id,
                    kind=step.kind,
                    status="failed",
                    summary=str(e)[:400],
                )
                merged, ru, ok = await _replan_merge(
                    client,
                    body,
                    plan,
                    trace,
                    step,
                    working_context,
                    str(e),
                    daytona_available,
                    replan_used,
                    i,
                    steps,
                    usage_segments,
                )
                if ok:
                    steps = merged
                    replan_used = ru
                    continue
                working_context += f"\n### 步骤 {step.id}（HTML）异常\n{str(e)[:500]}\n"
                i += 1
                continue

            usage_segments.append(("chat_html", p_tok, c_tok, lat))
            preview_citations, preview_code, preview_html = _merge_preview(
                resp, citations=preview_citations, code=preview_code, html=preview_html
            )
            last_assistant = resp.message.content or last_assistant
            last_tool_calls = None
            hlen = len(resp.html_content or "")
            summ = f"HTML 约 {hlen} 字符" if hlen else (resp.message.content or "")[:400]
            trace[-1] = ExecutionStepTrace(
                step_id=step.id,
                kind=step.kind,
                status="done",
                summary=summ,
            )
            working_context += f"\n### 步骤 {step.id}（HTML）\n{summ}\n"
            i += 1
            continue

        if step.kind == "synthesize":
            trace.append(ExecutionStepTrace(step_id=step.id, kind=step.kind, status="running", summary=""))
            try:
                resp, seg = await _run_synthesize(client, body.messages, working_context)
            except Exception as e:
                logger.exception("synthesize step error: %s", e)
                trace[-1] = ExecutionStepTrace(
                    step_id=step.id,
                    kind=step.kind,
                    status="failed",
                    summary=str(e)[:400],
                )
                merged, ru, ok = await _replan_merge(
                    client,
                    body,
                    plan,
                    trace,
                    step,
                    working_context,
                    str(e),
                    daytona_available,
                    replan_used,
                    i,
                    steps,
                    usage_segments,
                )
                if ok:
                    steps = merged
                    replan_used = ru
                    continue
                last_assistant = last_assistant or f"汇总步骤失败：{e!s}"
                i += 1
                continue

            usage_segments.append(seg)
            last_assistant = resp.message.content or last_assistant
            last_tool_calls = None
            summ = (resp.message.content or "")[:800]
            trace[-1] = ExecutionStepTrace(
                step_id=step.id,
                kind=step.kind,
                status="done",
                summary=summ[:400],
            )
            working_context += f"\n### 步骤 {step.id}（汇总）\n{summ}\n"
            i += 1
            continue

        trace.append(
            ExecutionStepTrace(step_id=step.id, kind=step.kind, status="skipped", summary="未知步骤类型")
        )
        i += 1

    intent = _final_intent(len(trace), replan_used, first_kind)
    out = ChatResponse(
        message=ChatMessage(role="assistant", content=last_assistant or "执行完成。"),
        tool_calls=last_tool_calls,
        citation_chunks=preview_citations,
        intent=intent,
        code_result=preview_code,
        html_content=preview_html,
        plan_summary=plan_summary,
        execution_trace=trace,
    )
    return OrchestrationResult(response=out, usage_segments=usage_segments)
