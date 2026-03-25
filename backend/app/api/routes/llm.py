"""LLM 对话接口：用户对话 + 工具调用（检索类工具）。"""
import json
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.repositories import BillingRepository, KBRepository, UsageRepository
from app.api.schemas.llm import ChatMessage, ChatRequest, ChatResponse, CitationChunk
from app.services.llm_tools import get_tool_definitions, execute_tool
from app.services.intent_router import route as intent_route
from app.services.agents import coding_chat, html_chat
from app.prompts import get_kb_agent_prompt

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
    # 粗略估算：英文约 4 chars/token；中文更接近 1~2 chars/token，但这里用保守估计便于拒绝余额不足
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

    daytona_available = bool(settings.daytona_api_key)
    intent = await intent_route(body.messages, daytona_available=daytona_available)
    logger.info("chat intent: %s", intent)

    if intent == "code":
        if settings.billing_enabled:
            worst = _estimate_prompt_tokens(_to_openai_messages(body.messages)) + 2 * int(settings.billing_max_completion_tokens or 1024)
            if acct.balance_cents < _cost_cents(worst, settings.llm_model):
                raise HTTPException(402, "Insufficient balance")
        resp, prompt_tok, comp_tok = await coding_chat(client, body.messages)
        total_tok = prompt_tok + comp_tok
        ev = await usage_repo.create_event(user_id=uid, kb_id=body.kb_id, conversation_id=None, model=settings.llm_model, request_type="chat_coding", prompt_tokens=prompt_tok, completion_tokens=comp_tok, total_tokens=prompt_tok + comp_tok, latency_ms=0)
        if settings.billing_enabled and total_tok > 0:
            cost = _cost_cents(total_tok, settings.llm_model)
            if cost > 0:
                try:
                    await billing_repo.debit(user_id=uid, amount_cents=cost, reason="usage_debit", ref_type="llm_usage_event", ref_id=ev.id, require_sufficient_balance=True)
                except ValueError:
                    raise HTTPException(402, "Insufficient balance")
        return resp

    if intent == "html":
        if settings.billing_enabled:
            worst = _estimate_prompt_tokens(_to_openai_messages(body.messages)) + int(settings.billing_max_completion_tokens or 2048)
            if acct.balance_cents < _cost_cents(worst, settings.llm_model):
                raise HTTPException(402, "Insufficient balance")
        resp, prompt_tok, comp_tok = await html_chat(client, body.messages)
        total_tok = prompt_tok + comp_tok
        ev = await usage_repo.create_event(user_id=uid, kb_id=body.kb_id, conversation_id=None, model=settings.llm_model, request_type="chat_html", prompt_tokens=prompt_tok, completion_tokens=comp_tok, total_tokens=total_tok, latency_ms=0)
        if settings.billing_enabled and total_tok > 0:
            cost = _cost_cents(total_tok, settings.llm_model)
            if cost > 0:
                try:
                    await billing_repo.debit(user_id=uid, amount_cents=cost, reason="usage_debit", ref_type="llm_usage_event", ref_id=ev.id, require_sufficient_balance=True)
                except ValueError:
                    raise HTTPException(402, "Insufficient balance")
        return resp

    tools = get_tool_definitions(body.kb_id)
    msgs = _to_openai_messages(body.messages)
    if not any(m.get("role") == "system" for m in msgs):
        msgs = [{"role": "system", "content": get_kb_agent_prompt()}] + msgs

    if settings.billing_enabled:
        prompt_est = _estimate_prompt_tokens(msgs)
        worst_total = prompt_est + int(settings.billing_max_completion_tokens or 0)
        worst_cost = _cost_cents(worst_total, settings.llm_model)
        if acct.balance_cents < worst_cost:
            raise HTTPException(402, "Insufficient balance")

    last_user = next((m.get("content") for m in reversed(msgs) if m.get("role") == "user"), "")
    logger.info("chat request: kb_id=%s tools=%s last_user_len=%s last_user_preview=%s", body.kb_id, len(tools) if tools else 0, len(last_user), (last_user or "")[:200])

    t0 = time.perf_counter()
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=msgs,
        tools=tools if tools else None,
        tool_choice="auto" if tools else None,
        max_tokens=settings.billing_max_completion_tokens if settings.billing_enabled else None,
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    choice = response.choices[0] if response.choices else None
    if not choice:
        raise HTTPException(502, "Empty model response")

    msg = choice.message
    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", 0) or 0)
    ev = await usage_repo.create_event(
        user_id=uid,
        kb_id=body.kb_id,
        conversation_id=None,
        model=settings.llm_model,
        request_type="chat_first",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
    )
    if settings.billing_enabled:
        cost = _cost_cents(total_tokens, settings.llm_model)
        if cost > 0:
            try:
                await billing_repo.debit(
                    user_id=uid,
                    amount_cents=cost,
                    reason="usage_debit",
                    ref_type="llm_usage_event",
                    ref_id=ev.id,
                    require_sufficient_balance=True,
                )
            except ValueError:
                raise HTTPException(402, "Insufficient balance")

    tool_calls = getattr(msg, "tool_calls", None) or []
    content_preview = (msg.content or "")[:300]
    logger.info("chat first response: has_tool_calls=%s count=%s content_preview=%s", bool(tool_calls), len(tool_calls), content_preview)

    if not tool_calls:
        return ChatResponse(
            message=ChatMessage(role="assistant", content=msg.content or ""),
            tool_calls=None,
            citation_chunks=None,
            intent="kb",
        )

    # 执行所有工具调用，把结果追加到对话，再请求一次 completion
    logger.info("chat tool_calls: kb_id=%s count=%s names=%s", body.kb_id, len(tool_calls), [getattr(t, "function", None) and getattr(t.function, "name", None) for t in tool_calls])
    tool_calls_payload = []
    tool_results = []
    all_chunks: list[dict] = []
    for tc in tool_calls:
        name = getattr(tc, "function", None) and getattr(tc.function, "name", None)
        args_str = getattr(tc.function, "arguments", None) or "{}"
        try:
            args = json.loads(args_str)
        except json.JSONDecodeError:
            args = {}
        result = execute_tool(body.kb_id, name or "", args)
        logger.info("execute_tool: name=%s query=%s result_count=%s", name, args.get("query"), len(result))
        for r in result[:10]:
            meta = r.get("metadata") or {}
            all_chunks.append({
                "chunk_text": r.get("chunk_text") or "",
                "source_id": meta.get("source_id"),
                "source_type": meta.get("source_type"),
                "metadata": meta,
            })
        result_text = json.dumps(
            [{"chunk_text": r.get("chunk_text"), "score": r.get("score"), "id": r.get("id")} for r in result[:10]],
            ensure_ascii=False,
        )
        tool_calls_payload.append({"id": tc.id, "type": "function", "function": {"name": name, "arguments": args_str}})
        tool_results.append((tc.id, result_text))
    msgs.append({"role": "assistant", "content": msg.content or None, "tool_calls": tool_calls_payload})
    for tid, content in tool_results:
        msgs.append({"role": "tool", "tool_call_id": tid, "content": content})

    t1 = time.perf_counter()
    final = await client.chat.completions.create(
        model=settings.llm_model,
        messages=msgs,
        max_tokens=settings.billing_max_completion_tokens if settings.billing_enabled else None,
    )
    latency2_ms = int((time.perf_counter() - t1) * 1000)
    final_choice = final.choices[0] if final.choices else None
    if not final_choice:
        raise HTTPException(502, "Empty model response after tool use")
    usage2 = getattr(final, "usage", None)
    prompt_tokens2 = int(getattr(usage2, "prompt_tokens", 0) or 0)
    completion_tokens2 = int(getattr(usage2, "completion_tokens", 0) or 0)
    total_tokens2 = int(getattr(usage2, "total_tokens", 0) or 0)
    ev2 = await usage_repo.create_event(
        user_id=uid,
        kb_id=body.kb_id,
        conversation_id=None,
        model=settings.llm_model,
        request_type="chat_final",
        prompt_tokens=prompt_tokens2,
        completion_tokens=completion_tokens2,
        total_tokens=total_tokens2,
        latency_ms=latency2_ms,
    )
    if settings.billing_enabled:
        cost2 = _cost_cents(total_tokens2, settings.llm_model)
        if cost2 > 0:
            try:
                await billing_repo.debit(
                    user_id=uid,
                    amount_cents=cost2,
                    reason="usage_debit",
                    ref_type="llm_usage_event",
                    ref_id=ev2.id,
                    require_sufficient_balance=True,
                )
            except ValueError:
                raise HTTPException(402, "Insufficient balance")
    citation_chunks = [CitationChunk(**c) for c in all_chunks] if all_chunks else None
    return ChatResponse(
        message=ChatMessage(role="assistant", content=final_choice.message.content or ""),
        tool_calls=[{"name": getattr(tc.function, "name", None), "arguments": getattr(tc.function, "arguments", None)} for tc in tool_calls],
        citation_chunks=citation_chunks,
        intent="kb",
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
