"""意图路由：根据用户消息判断为 kb / code / html，供 chat 派发。"""
import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.api.schemas.llm import ChatMessage
from app.core.config import settings
from app.prompts import get_intent_router_prompt

logger = logging.getLogger(__name__)

INTENT_KB = "kb"
INTENT_CODE = "code"
INTENT_HTML = "html"


def _openai_client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise ValueError("LLM not configured (OPENAI_API_KEY)")
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


async def route(messages: list[ChatMessage], daytona_available: bool = True) -> str:
    """
    根据对话历史判断当前意图。
    :param messages: 当前对话消息列表
    :param daytona_available: 是否配置了 Daytona；若 False，code/html 会回退为 kb
    :return: "kb" | "code" | "html"
    """
    last_user = next(
        (m.content for m in reversed(messages) if m.role == "user"),
        "",
    ).strip()
    if not last_user:
        return INTENT_KB

    msgs = [{"role": "system", "content": get_intent_router_prompt()}]
    for m in messages[-5:]:  # 只取最近几条以控制 token
        msgs.append({"role": m.role, "content": m.content or ""})

    try:
        client = _openai_client()
        resp = await client.chat.completions.create(
            model=settings.llm_model,
            messages=msgs,
            max_tokens=32,
        )
        content = (resp.choices[0].message.content or "").strip()
        # 尝试解析 JSON
        for raw in (content, content.split("\n")[0], content.replace("'", '"')):
            try:
                obj = json.loads(raw)
                intent = (obj.get("intent") or INTENT_KB).lower()
                if intent not in (INTENT_KB, INTENT_CODE, INTENT_HTML):
                    intent = INTENT_KB
                if not daytona_available and intent in (INTENT_CODE, INTENT_HTML):
                    intent = INTENT_KB
                return intent
            except json.JSONDecodeError:
                continue
    except Exception as e:
        logger.warning("intent_router route error: %s", e)
    return INTENT_KB
