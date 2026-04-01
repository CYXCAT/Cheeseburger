"""Replanner：步骤失败后再规划。"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from app.api.schemas.llm import ChatMessage, ExecutionStepTrace, PlanStep, PlannerPlan
from app.core.config import settings
from app.prompts import get_replanner_prompt
from app.services.orchestration.plan_schema import normalize_plan_dict, parse_planner_response

if TYPE_CHECKING:
    from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


async def run_replanner(
    client: AsyncOpenAI,
    messages: list[ChatMessage],
    *,
    original_plan: PlannerPlan,
    completed_trace: list[ExecutionStepTrace],
    failed_step: PlanStep,
    error_summary: str,
    working_context: str,
    daytona_available: bool,
) -> tuple[PlannerPlan, int, int]:
    sys = get_replanner_prompt(max_steps=settings.planner_max_steps)
    if not daytona_available:
        sys += "\n\n系统约束：沙箱不可用（code_forbidden）。禁止使用 kind code。"
    payload = {
        "original_reasoning": original_plan.reasoning_summary,
        "failed_step": {"id": failed_step.id, "kind": failed_step.kind, "goal": failed_step.goal},
        "error": error_summary,
        "completed_steps": [{"id": t.step_id, "kind": t.kind, "status": t.status, "summary": t.summary} for t in completed_trace],
        "working_context": working_context[:8000],
    }
    user_text = "请根据以下 JSON 再规划剩余任务，只输出规划 JSON：\n" + json.dumps(payload, ensure_ascii=False)
    msgs: list[dict] = [{"role": "system", "content": sys}]
    for m in messages[-8:]:
        msgs.append({"role": m.role, "content": m.content or ""})
    msgs.append({"role": "user", "content": user_text})
    try:
        resp = await client.chat.completions.create(
            model=settings.llm_model,
            messages=msgs,
            max_tokens=settings.planner_max_completion_tokens,
        )
        usage = getattr(resp, "usage", None)
        pt = int(getattr(usage, "prompt_tokens", 0) or 0)
        ct = int(getattr(usage, "completion_tokens", 0) or 0)
        content = (resp.choices[0].message.content or "").strip() if resp.choices else ""
        plan = parse_planner_response(content, daytona_available=daytona_available)
        if plan is None:
            logger.warning("replanner parse failed, synthesize fallback")
            fb = normalize_plan_dict(
                {
                    "reasoning_summary": "再规划解析失败，改为说明现状。",
                    "steps": [
                        {
                            "id": "1",
                            "kind": "synthesize",
                            "goal": "向用户说明执行失败原因并给出建议",
                        }
                    ],
                },
                daytona_available=daytona_available,
            )
            return fb, pt, ct
        return plan, pt, ct
    except Exception as e:
        logger.warning("replanner error: %s", e)
        fb = normalize_plan_dict(
            {
                "reasoning_summary": f"再规划调用异常: {e!s}",
                "steps": [{"id": "1", "kind": "synthesize", "goal": "向用户说明错误并给出建议"}],
            },
            daytona_available=daytona_available,
        )
        return fb, 0, 0
