"""Coding Agent：生成并调用 code_run 在沙盒中执行代码，与主对话共享 messages。"""
import json
import logging
import time
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
) -> tuple[ChatResponse, list[tuple[str, int, int, int]]]:
    """
    执行 Coding Agent：支持沙箱非零退出后的多轮修正（code_run 工具循环），最后总结。
    返回 (ChatResponse, [(request_type, prompt_tokens, completion_tokens, latency_ms), ...])。
    """
    msgs = _to_openai_messages(messages)
    if not any(m.get("role") == "system" for m in msgs):
        msgs = [{"role": "system", "content": get_coding_agent_prompt()}] + msgs

    usage_segments: list[tuple[str, int, int, int]] = []
    code_result: dict[str, Any] | None = None
    max_attempts = max(1, 1 + int(settings.code_max_sandbox_retries))

    for attempt in range(max_attempts):
        t0 = time.perf_counter()
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=msgs,
            tools=[CODE_RUN_TOOL],
            tool_choice="required",
            max_tokens=settings.billing_max_completion_tokens if settings.billing_enabled else 1024,
        )
        choice = response.choices[0] if response.choices else None
        usage = getattr(response, "usage", None)
        p = int(getattr(usage, "prompt_tokens", 0) or 0)
        c = int(getattr(usage, "completion_tokens", 0) or 0)
        lat = int((time.perf_counter() - t0) * 1000)
        rt = "chat_coding" if attempt == 0 else "chat_coding_retry"
        usage_segments.append((rt, p, c, lat))

        if not choice:
            return (
                ChatResponse(
                    message=ChatMessage(role="assistant", content="模型未返回有效内容。"),
                    intent="code",
                    code_result=code_result,
                ),
                usage_segments,
            )

        msg = choice.message
        tool_calls = getattr(msg, "tool_calls", None) or []

        if not tool_calls:
            content = (msg.content or "").strip()
            return (
                ChatResponse(
                    message=ChatMessage(role="assistant", content=content or "未产生工具调用。"),
                    intent="code",
                    code_result=code_result,
                ),
                usage_segments,
            )

        msgs.append({
            "role": "assistant",
            "content": msg.content or None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": getattr(tc.function, "name", None),
                        "arguments": getattr(tc.function, "arguments", None),
                    },
                }
                for tc in tool_calls
            ],
        })

        exit_ok = True
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
            ec = int(res.get("exit_code", -1) if isinstance(res, dict) else -1)
            if ec != 0:
                exit_ok = False
            msgs.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})

        if exit_ok:
            break
        if attempt >= max_attempts - 1:
            break

    t1 = time.perf_counter()
    final = await client.chat.completions.create(
        model=settings.llm_model,
        messages=msgs,
        max_tokens=settings.billing_max_completion_tokens if settings.billing_enabled else 512,
    )
    usage2 = getattr(final, "usage", None)
    p2 = int(getattr(usage2, "prompt_tokens", 0) or 0)
    c2 = int(getattr(usage2, "completion_tokens", 0) or 0)
    lat2 = int((time.perf_counter() - t1) * 1000)
    usage_segments.append(("chat_coding_final", p2, c2, lat2))
    final_choice = final.choices[0] if final.choices else None
    content = (final_choice.message.content or "").strip() if final_choice else "执行完成。"
    return (
        ChatResponse(
            message=ChatMessage(role="assistant", content=content),
            intent="code",
            code_result=code_result,
        ),
        usage_segments,
    )
