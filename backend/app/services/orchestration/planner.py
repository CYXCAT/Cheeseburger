"""Planner：生成结构化任务计划。"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.api.schemas.llm import ChatMessage, PlanStep, PlannerPlan, PlannerDebugResponse
from app.core.config import settings
from app.prompts import get_planner_prompt
from app.services.intent_router import route as intent_route
from app.services.orchestration.plan_schema import parse_planner_response

if TYPE_CHECKING:
    from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


async def _fallback_plan_async(
    messages: list[ChatMessage],
    *,
    daytona_available: bool,
) -> tuple[PlannerPlan, int, int]:
    intent = await intent_route(messages, daytona_available=daytona_available)
    last_user = next((m.content.strip() for m in reversed(messages) if m.role == "user"), "") or "回答用户问题"
    kind_map = {"kb": "knowledge", "code": "code", "html": "html"}
    k = kind_map.get(intent, "knowledge")
    if not daytona_available and k == "code":
        k = "synthesize"
    plan = PlannerPlan(
        reasoning_summary="已按单步任务直接处理。",
        steps=[PlanStep(id="1", kind=k, goal=last_user[:2000])],
    )
    return plan, 0, 0


def _messages_for_planner(messages: list[ChatMessage], *, daytona_available: bool) -> list[dict]:
    sys = get_planner_prompt(max_steps=settings.planner_max_steps)
    if not daytona_available:
        sys += "\n\n系统约束：沙箱当前不可用（code_forbidden）。禁止在 steps 中使用 kind 为 code 的步骤。"
    else:
        sys += (
            "\n\n系统约束：沙箱当前**可用**。用户若要求「运行/执行/run 代码」或「示例并运行」，"
            "计划中必须包含 kind 为 code 的步骤（可 knowledge → code → synthesize）；"
            "勿用「仅检索 + 仅 synthesize」代替真实执行。"
        )
    out: list[dict] = [{"role": "system", "content": sys}]
    for m in messages[-12:]:
        out.append({"role": m.role, "content": m.content or ""})
    return out


async def _invoke_planner_model(
    client: AsyncOpenAI,
    messages: list[ChatMessage],
    *,
    daytona_available: bool,
) -> tuple[str, int, int, bool]:
    """
    调用 Planner LLM。
    返回 (raw_content, prompt_tokens, completion_tokens, used_json_object_mode)。
    """
    msgs = _messages_for_planner(messages, daytona_available=daytona_available)
    kwargs = dict(
        model=settings.llm_model,
        messages=msgs,
        max_tokens=settings.planner_max_completion_tokens,
    )
    used_json = False
    try:
        resp = await client.chat.completions.create(
            **kwargs,
            response_format={"type": "json_object"},
        )
        used_json = True
    except Exception as fmt_err:
        logger.debug("planner response_format json_object not supported: %s", fmt_err)
        resp = await client.chat.completions.create(**kwargs)
    usage = getattr(resp, "usage", None)
    pt = int(getattr(usage, "prompt_tokens", 0) or 0)
    ct = int(getattr(usage, "completion_tokens", 0) or 0)
    content = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    return content, pt, ct, used_json


async def run_planner(
    client: AsyncOpenAI,
    messages: list[ChatMessage],
    *,
    daytona_available: bool,
) -> tuple[PlannerPlan, int, int]:
    """
    调用模型生成计划；解析失败则回退意图路由单步计划。
    返回 (plan, prompt_tokens, completion_tokens)。
    """
    try:
        content, pt, ct, _used_json = await _invoke_planner_model(
            client, messages, daytona_available=daytona_available
        )
        plan = parse_planner_response(content, daytona_available=daytona_available)
        if plan is None:
            logger.warning(
                "planner JSON parse failed, fallback intent. preview=%s",
                (content[:500] + "…") if len(content) > 500 else content,
            )
            return await _fallback_plan_async(messages, daytona_available=daytona_available)
        return plan, pt, ct
    except Exception as e:
        logger.warning("planner call error: %s", e)
        return await _fallback_plan_async(messages, daytona_available=daytona_available)


async def debug_planner(
    client: AsyncOpenAI,
    messages: list[ChatMessage],
    *,
    daytona_available: bool,
    include_fallback_preview: bool = True,
) -> PlannerDebugResponse:
    """
    仅调试：返回原始输出、是否解析成功、规范化计划、可选回退计划预览。不计入业务用量（由路由层决定是否记账）。
    """
    sys_preview = _messages_for_planner(messages, daytona_available=daytona_available)[0].get("content", "") or ""
    sys_preview = sys_preview[:2000] + ("…" if len(sys_preview) > 2000 else "")

    try:
        content, pt, ct, used_json = await _invoke_planner_model(
            client, messages, daytona_available=daytona_available
        )
    except Exception as e:
        logger.exception("debug_planner invoke error: %s", e)
        return PlannerDebugResponse(
            model=settings.llm_model,
            raw_content="",
            prompt_tokens=0,
            completion_tokens=0,
            used_json_object_mode=False,
            parse_ok=False,
            plan=None,
            fallback_plan=None,
            system_prompt_preview=sys_preview,
            invoke_error=str(e),
        )

    parsed = parse_planner_response(content, daytona_available=daytona_available)
    fb: PlannerPlan | None = None
    if include_fallback_preview and parsed is None:
        fb_plan, _, _ = await _fallback_plan_async(messages, daytona_available=daytona_available)
        fb = fb_plan

    return PlannerDebugResponse(
        model=settings.llm_model,
        raw_content=content,
        prompt_tokens=pt,
        completion_tokens=ct,
        used_json_object_mode=used_json,
        parse_ok=parsed is not None,
        plan=parsed,
        fallback_plan=fb,
        system_prompt_preview=sys_preview,
        invoke_error=None,
    )
