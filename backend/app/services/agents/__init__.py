"""多 Agent 模块：Coding / HTML 等，与主对话共享 messages。"""
from app.services.agents.coding_agent import chat as coding_chat
from app.services.agents.html_agent import chat as html_chat

__all__ = ["coding_chat", "html_chat"]
