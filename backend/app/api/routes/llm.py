"""LLM 对话接口：用户对话 + 工具调用（检索类工具）。"""
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.repositories import KBRepository
from app.api.schemas.llm import ChatMessage, ChatRequest, ChatResponse, CitationChunk
from app.services.llm_tools import get_tool_definitions, execute_tool

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


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(body.kb_id, user_id, db)
    client = _openai_client()
    tools = get_tool_definitions(body.kb_id)
    msgs = _to_openai_messages(body.messages)
    # 注入系统提示：强制在知识库相关问题时先调用检索，不要反问用户
    system_msg = (
        "你是知识库助手。你拥有检索工具：semantic_search、keyword_search、hybrid_search。\n"
        "规则：当用户询问「文档内容」「查找数据库」「总结/叙述/介绍知识库内容」或任何与知识库资料相关的问题时，"
        "你必须先调用其中一个检索工具（用用户原句或提取的关键词作为 query），再根据检索结果回答。"
        "禁止先反问「请问您要查什么」「请提供具体信息」；若用户表述笼统，就用用户原句去检索。\n"
        "只有用户明确与知识库无关（如打招呼、闲聊）时才可直接回复、不调工具。"
    )
    if not any(m.get("role") == "system" for m in msgs):
        msgs = [{"role": "system", "content": system_msg}] + msgs

    last_user = next((m.get("content") for m in reversed(msgs) if m.get("role") == "user"), "")
    logger.info("chat request: kb_id=%s tools=%s last_user_len=%s last_user_preview=%s", body.kb_id, len(tools) if tools else 0, len(last_user), (last_user or "")[:200])

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=msgs,
        tools=tools if tools else None,
        tool_choice="auto" if tools else None,
    )
    choice = response.choices[0] if response.choices else None
    if not choice:
        raise HTTPException(502, "Empty model response")

    msg = choice.message
    tool_calls = getattr(msg, "tool_calls", None) or []
    content_preview = (msg.content or "")[:300]
    logger.info("chat first response: has_tool_calls=%s count=%s content_preview=%s", bool(tool_calls), len(tool_calls), content_preview)

    if not tool_calls:
        return ChatResponse(
            message=ChatMessage(role="assistant", content=msg.content or ""),
            tool_calls=None,
            citation_chunks=None,
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

    final = await client.chat.completions.create(
        model=settings.llm_model,
        messages=msgs,
    )
    final_choice = final.choices[0] if final.choices else None
    if not final_choice:
        raise HTTPException(502, "Empty model response after tool use")
    citation_chunks = [CitationChunk(**c) for c in all_chunks] if all_chunks else None
    return ChatResponse(
        message=ChatMessage(role="assistant", content=final_choice.message.content or ""),
        tool_calls=[{"name": getattr(tc.function, "name", None), "arguments": getattr(tc.function, "arguments", None)} for tc in tool_calls],
        citation_chunks=citation_chunks,
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
