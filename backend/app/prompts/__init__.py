"""统一管理各 Agent / Router 的 prompt 文本，便于修改与版本管理。"""
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent


def _load(name: str) -> str:
    path = _PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


# 按需加载，避免启动时读盘（也可改为模块级常量一次性加载）
def get_intent_router_prompt() -> str:
    return _load("intent_router")


def get_kb_agent_prompt() -> str:
    return _load("kb_agent")


def get_coding_agent_prompt() -> str:
    return _load("coding_agent")


def get_html_agent_prompt() -> str:
    return _load("html_agent")


# 工具定义（结构化，保留在代码中；若需可插拔可再拆为 JSON）
CODE_RUN_TOOL = {
    "type": "function",
    "function": {
        "name": "code_run",
        "description": "在沙盒中执行一段代码。你必须生成可独立运行的代码（如 Python 片段），然后调用本工具执行。",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要执行的代码内容"},
                "language": {"type": "string", "description": "语言，如 python、javascript", "default": "python"},
            },
            "required": ["code"],
        },
    },
}

__all__ = [
    "get_intent_router_prompt",
    "get_kb_agent_prompt",
    "get_coding_agent_prompt",
    "get_html_agent_prompt",
    "CODE_RUN_TOOL",
]
