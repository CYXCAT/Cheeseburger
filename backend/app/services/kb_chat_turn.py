"""知识库 Agent 单轮：工具检索 + 可选二次 completion。供 llm 路由与编排器共用。"""
from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING

from app.api.schemas.llm import ChatMessage, ChatResponse, CitationChunk
from app.core.config import settings
from app.prompts import get_kb_agent_prompt
from app.services.llm_tools import execute_tool, get_tool_definitions

if TYPE_CHECKING:
    from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


def _to_openai_messages(messages: list[ChatMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in messages]


async def run_kb_agent_turn(
    client: AsyncOpenAI,
    kb_id: int,
    messages: list[ChatMessage],
    *,
    first_event_type: str = "chat_first",
    final_event_type: str = "chat_final",
) -> tuple[ChatResponse, list[tuple[str, int, int, int]]]:
    """
    返回 (ChatResponse, [(request_type, prompt_tokens, completion_tokens, latency_ms), ...])。
    """
    usage_segments: list[tuple[str, int, int, int]] = []
    tools = get_tool_definitions(kb_id)
    msgs = _to_openai_messages(messages)
    if not any(m.get("role") == "system" for m in msgs):
        msgs = [{"role": "system", "content": get_kb_agent_prompt()}] + msgs

    last_user = next((m.get("content") for m in reversed(msgs) if m.get("role") == "user"), "")
    logger.info(
        "kb_agent_turn: kb_id=%s tools=%s last_user_preview=%s",
        kb_id,
        len(tools) if tools else 0,
        (last_user or "")[:200],
    )

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
        return (
            ChatResponse(message=ChatMessage(role="assistant", content="模型未返回有效内容。"), intent="kb"),
            [(first_event_type, 0, 0, latency_ms)],
        )

    msg = choice.message
    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    usage_segments.append((first_event_type, prompt_tokens, completion_tokens, latency_ms))

    tool_calls = getattr(msg, "tool_calls", None) or []
    if not tool_calls:
        return (
            ChatResponse(
                message=ChatMessage(role="assistant", content=msg.content or ""),
                tool_calls=None,
                citation_chunks=None,
                intent="kb",
            ),
            usage_segments,
        )

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
        result = execute_tool(kb_id, name or "", args)
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
        return (
            ChatResponse(
                message=ChatMessage(role="assistant", content="工具调用后模型无响应。"),
                tool_calls=[{"name": getattr(tc.function, "name", None), "arguments": getattr(tc.function, "arguments", None)} for tc in tool_calls],
                citation_chunks=[CitationChunk(**c) for c in all_chunks] if all_chunks else None,
                intent="kb",
            ),
            usage_segments,
        )
    usage2 = getattr(final, "usage", None)
    prompt_tokens2 = int(getattr(usage2, "prompt_tokens", 0) or 0)
    completion_tokens2 = int(getattr(usage2, "completion_tokens", 0) or 0)
    usage_segments.append((final_event_type, prompt_tokens2, completion_tokens2, latency2_ms))

    citation_chunks = [CitationChunk(**c) for c in all_chunks] if all_chunks else None
    return (
        ChatResponse(
            message=ChatMessage(role="assistant", content=final_choice.message.content or ""),
            tool_calls=[{"name": getattr(tc.function, "name", None), "arguments": getattr(tc.function, "arguments", None)} for tc in tool_calls],
            citation_chunks=citation_chunks,
            intent="kb",
        ),
        usage_segments,
    )
