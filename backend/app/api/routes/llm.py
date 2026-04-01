"""LLM 对话接口：Planner 拆解 + 编排执行（知识库工具 / 代码沙箱 / HTML）。"""
import logging

from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.repositories import BillingRepository, KBRepository, UsageRepository
from app.api.schemas.llm import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    OrchestrateDebugResponse,
    PlannerDebugRequest,
    PlannerDebugResponse,
    UsageSegmentOut,
)
from app.services.orchestration.orchestrator import run_orchestration
from app.services.orchestration.planner import debug_planner, run_planner

router = APIRouter()


async def _get_kb_or_404(kb_id: int, user_id: str, db: AsyncSession):
    repo = KBRepository(db)
    kb = await repo.get_kb(kb_id, user_id)
    if not kb:
        raise HTTPException(404, "Knowledge base not found")
    return kb


def _openai_client():
    if not settings.openai_api_key:
        raise HTTPException(503, "LLM not configured (OPENAI_API_KEY)")
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def _to_openai_messages(messages: list[ChatMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in messages]


def _estimate_prompt_tokens(messages: list[dict]) -> int:
    total_chars = 0
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            total_chars += len(c)
    return max(1, total_chars // 3)


def _price_cents_per_1k(model: str) -> int:
    return int(settings.model_prices_cents_per_1k.get(model, 0))


def _cost_cents(total_tokens: int, model: str) -> int:
    price = _price_cents_per_1k(model)
    if price <= 0 or total_tokens <= 0:
        return 0
    return (total_tokens * price + 999) // 1000


async def _record_usage_and_debit(
    *,
    usage_repo: UsageRepository,
    billing_repo: BillingRepository,
    user_id: int,
    kb_id: int,
    request_type: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
    model: str,
) -> None:
    total_tokens = prompt_tokens + completion_tokens
    ev = await usage_repo.create_event(
        user_id=user_id,
        kb_id=kb_id,
        conversation_id=None,
        model=model,
        request_type=request_type,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
    )
    if settings.billing_enabled and total_tokens > 0:
        cost = _cost_cents(total_tokens, model)
        if cost > 0:
            try:
                await billing_repo.debit(
                    user_id=user_id,
                    amount_cents=cost,
                    reason="usage_debit",
                    ref_type="llm_usage_event",
                    ref_id=ev.id,
                    require_sufficient_balance=True,
                )
            except ValueError:
                raise HTTPException(402, "Insufficient balance")


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(body.kb_id, user_id, db)
    client = _openai_client()
    uid = int(user_id)
    billing_repo = BillingRepository(db)
    usage_repo = UsageRepository(db)
    acct = await billing_repo.get_or_create_account(uid, currency=settings.billing_currency)

    msgs_dict = _to_openai_messages(body.messages)
    if settings.billing_enabled:
        prompt_est = _estimate_prompt_tokens(msgs_dict)
        worst = prompt_est + int(settings.planner_max_completion_tokens)
        worst += (settings.planner_max_steps + 6) * int(settings.billing_max_completion_tokens or 1024)
        if acct.balance_cents < _cost_cents(worst, settings.llm_model):
            raise HTTPException(402, "Insufficient balance")

    daytona_available = bool(settings.daytona_api_key)
    plan, p_pt, p_ct = await run_planner(client, body.messages, daytona_available=daytona_available)
    logger.info(
        "chat planner: steps=%s summary_preview=%s",
        len(plan.steps),
        (plan.reasoning_summary or "")[:120],
    )

    await _record_usage_and_debit(
        usage_repo=usage_repo,
        billing_repo=billing_repo,
        user_id=uid,
        kb_id=body.kb_id,
        request_type="planner",
        prompt_tokens=p_pt,
        completion_tokens=p_ct,
        latency_ms=0,
        model=settings.llm_model,
    )

    single_kb = len(plan.steps) == 1 and plan.steps[0].kind == "knowledge"
    kb_usage = ("chat_first", "chat_final") if single_kb else ("orch_kb_first", "orch_kb_final")

    orch = await run_orchestration(
        client,
        body,
        plan,
        daytona_available=daytona_available,
        plan_summary=plan.reasoning_summary,
        kb_usage_events=kb_usage,
    )

    for rt, pt, ct, lat in orch.usage_segments:
        await _record_usage_and_debit(
            usage_repo=usage_repo,
            billing_repo=billing_repo,
            user_id=uid,
            kb_id=body.kb_id,
            request_type=rt,
            prompt_tokens=pt,
            completion_tokens=ct,
            latency_ms=lat,
            model=settings.llm_model,
        )

    return orch.response


@router.post("/planner-debug", response_model=PlannerDebugResponse)
async def planner_debug(
    body: PlannerDebugRequest,
    _user_id: str = Depends(get_current_user_id),
):
    """
    仅调试 Planner：返回模型原始输出、解析结果、可选回退计划；不跑编排、不计业务用量。
    需在环境变量中开启 `PLANNER_DEBUG_ENABLED=true` 或 `DEBUG=true`。
    """
    if not (settings.planner_debug_enabled or settings.debug):
        raise HTTPException(
            404,
            "Planner debug disabled. Set PLANNER_DEBUG_ENABLED=true or DEBUG=true in .env",
        )
    client = _openai_client()
    daytona = (
        body.daytona_available
        if body.daytona_available is not None
        else bool(settings.daytona_api_key)
    )
    return await debug_planner(
        client,
        body.messages,
        daytona_available=daytona,
        include_fallback_preview=body.include_fallback_preview,
    )


@router.post("/orchestrate-debug", response_model=OrchestrateDebugResponse)
async def orchestrate_debug(
    body: ChatRequest,
    _user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Planner + 完整编排一次跑通，返回计划、最终 ChatResponse、分段用量；**不扣费**。
    需 `PLANNER_DEBUG_ENABLED=true` 或 `DEBUG=true`。
    """
    if not (settings.planner_debug_enabled or settings.debug):
        raise HTTPException(
            404,
            "Orchestrate debug disabled. Set PLANNER_DEBUG_ENABLED=true or DEBUG=true in .env",
        )
    await _get_kb_or_404(body.kb_id, _user_id, db)
    client = _openai_client()
    daytona_available = bool(settings.daytona_api_key)
    plan, p_pt, p_ct = await run_planner(client, body.messages, daytona_available=daytona_available)
    single_kb = len(plan.steps) == 1 and plan.steps[0].kind == "knowledge"
    kb_usage = ("chat_first", "chat_final") if single_kb else ("orch_kb_first", "orch_kb_final")
    orch = await run_orchestration(
        client,
        body,
        plan,
        daytona_available=daytona_available,
        plan_summary=plan.reasoning_summary,
        kb_usage_events=kb_usage,
    )
    segments = [
        UsageSegmentOut(
            request_type=rt,
            prompt_tokens=pt,
            completion_tokens=ct,
            latency_ms=lat,
        )
        for rt, pt, ct, lat in orch.usage_segments
    ]
    return OrchestrateDebugResponse(
        plan=plan,
        chat_response=orch.response,
        planner_prompt_tokens=p_pt,
        planner_completion_tokens=p_ct,
        orchestration_segments=segments,
    )


@router.get("/tools")
async def list_tools_info():
    """返回当前已注册的工具说明（供前端或文档使用）。"""
    return {
        "tools": [
            {"name": "semantic_search", "description": "在知识库中按语义相似度搜索文档片段"},
            {"name": "keyword_search", "description": "在知识库中按关键词匹配搜索"},
            {"name": "hybrid_search", "description": "混合搜索：语义+关键词"},
        ]
    }
