"""HTML Agent：根据用户需求生成完整 HTML 页面，与主对话共享 messages。"""
import re
import logging

from openai import AsyncOpenAI

from app.api.schemas.llm import ChatMessage, ChatResponse
from app.core.config import settings
from app.prompts import get_html_agent_prompt

logger = logging.getLogger(__name__)


def _to_openai_messages(messages: list[ChatMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content or ""} for m in messages]


def _extract_html(content: str) -> str | None:
    """从回复中提取 ```html ... ``` 或 ``` ... ``` 中的 HTML。"""
    if not content:
        return None
    # 优先 ```html ... ```
    m = re.search(r"```html\s*([\s\S]*?)```", content, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # 否则任意 ``` ... ``` 且内容像 HTML
    m = re.search(r"```\s*([\s\S]*?)```", content)
    if m:
        raw = m.group(1).strip()
        if raw.lstrip().lower().startswith(("<!doctype", "<html", "<head", "<body")):
            return raw
    # 整段就是 HTML
    if content.lstrip().lower().startswith("<!doctype") or "<html" in content.lower():
        return content.strip()
    return None


async def chat(
    client: AsyncOpenAI,
    messages: list[ChatMessage],
) -> tuple[ChatResponse, int, int]:
    """
    执行 HTML Agent：一次 completion，从回复中解析 HTML，返回扩展 ChatResponse 与 token 用量。
    """
    msgs = _to_openai_messages(messages)
    if not any(m.get("role") == "system" for m in msgs):
        msgs = [{"role": "system", "content": get_html_agent_prompt()}] + msgs

    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=msgs,
        max_tokens=settings.billing_max_completion_tokens if settings.billing_enabled else 2048,
    )
    choice = response.choices[0] if response.choices else None
    content = (choice.message.content or "").strip() if choice else ""
    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)

    html_content = _extract_html(content)
    if not html_content:
        html_content = None
    # 回复给用户看的文字：若有代码块则保留说明，否则用原文
    display_content = content if not html_content else f"已生成 HTML 页面（{len(html_content)} 字符），请在左侧预览中查看。"

    return (
        ChatResponse(
            message=ChatMessage(role="assistant", content=display_content),
            intent="html",
            html_content=html_content,
        ),
        prompt_tokens,
        completion_tokens,
    )
