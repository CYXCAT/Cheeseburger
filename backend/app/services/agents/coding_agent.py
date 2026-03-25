"""Coding Agent：生成并调用 code_run 在沙盒中执行代码，与主对话共享 messages。"""
import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.api.schemas.llm import ChatMessage, ChatResponse
from app.core.config import settings
from app.prompts import CODE_RUN_TOOL, get_coding_agent_prompt
from app.services.sandbox_service import execute as sandbox_execute

logger = logging.getLogger(__name__)


def _to_openai_messages(messages: list[ChatMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content or ""} for m in messages]


async def chat(
    client: AsyncOpenAI,
    messages: list[ChatMessage],
) -> tuple[ChatResponse, int, int]:
    """
    执行 Coding Agent：一次或两次 completion（含 code_run 工具调用），返回扩展 ChatResponse 与 token 用量。
    """
    msgs = _to_openai_messages(messages)
    if not any(m.get("role") == "system" for m in msgs):
        msgs = [{"role": "system", "content": get_coding_agent_prompt()}] + msgs

    total_prompt = 0
    total_completion = 0
    code_result: dict[str, Any] | None = None

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=msgs,
        tools=[CODE_RUN_TOOL],
        tool_choice="required",
        max_tokens=settings.billing_max_completion_tokens if settings.billing_enabled else 1024,
    )
    choice = response.choices[0] if response.choices else None
    if not choice:
        return (
            ChatResponse(
                message=ChatMessage(role="assistant", content="模型未返回有效内容。"),
                intent="code",
                code_result=None,
            ),
            0,
            0,
        )
    usage = getattr(response, "usage", None)
    total_prompt += int(getattr(usage, "prompt_tokens", 0) or 0)
    total_completion += int(getattr(usage, "completion_tokens", 0) or 0)

    msg = choice.message
    tool_calls = getattr(msg, "tool_calls", None) or []

    if not tool_calls:
        return (
            ChatResponse(
                message=ChatMessage(role="assistant", content=msg.content or ""),
                intent="code",
                code_result=code_result,
            ),
            total_prompt,
            total_completion,
        )

    msgs.append({
        "role": "assistant",
        "content": msg.content or None,
        "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": getattr(tc.function, "name", None), "arguments": getattr(tc.function, "arguments", None)}} for tc in tool_calls],
    })
    for tc in tool_calls:
        args_str = getattr(tc.function, "arguments", None) or "{}"
        try:
            args = json.loads(args_str)
        except json.JSONDecodeError:
            args = {}
        code = (args.get("code") or "").strip()
        language = (args.get("language") or "python").strip() or "python"
        res = sandbox_execute(code, language=language) if code else {"exit_code": -1, "result": "无代码"}
        code_result = res
        msgs.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})

    final = await client.chat.completions.create(
        model=settings.llm_model,
        messages=msgs,
        max_tokens=settings.billing_max_completion_tokens if settings.billing_enabled else 512,
    )
    usage2 = getattr(final, "usage", None)
    total_prompt += int(getattr(usage2, "prompt_tokens", 0) or 0)
    total_completion += int(getattr(usage2, "completion_tokens", 0) or 0)
    final_choice = final.choices[0] if final.choices else None
    content = (final_choice.message.content or "").strip() if final_choice else "执行完成。"
    return (
        ChatResponse(
            message=ChatMessage(role="assistant", content=content),
            intent="code",
            code_result=code_result,
        ),
        total_prompt,
        total_completion,
    )
