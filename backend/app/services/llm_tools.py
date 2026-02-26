"""LLM 工具：将知识库检索接口注册为可调用函数，供 Agent 使用。"""
from typing import Any

from app.services.pinecone_service import PineconeService


def semantic_search(kb_id: int, query: str, top_k: int = 10) -> list[dict]:
    """在知识库中做语义搜索。"""
    return PineconeService.search_semantic(kb_id, query, top_k=top_k)


def keyword_search(kb_id: int, query: str, top_k: int = 10) -> list[dict]:
    """在知识库中做关键词搜索。"""
    return PineconeService.search_keyword(kb_id, query, top_k=top_k)


def hybrid_search(kb_id: int, query: str, top_k: int = 10) -> list[dict]:
    """在知识库中做混合搜索（语义+关键词）。"""
    return PineconeService.search_hybrid(kb_id, query, top_k=top_k)


def get_tool_definitions(kb_id: int) -> list[dict[str, Any]]:
    """返回 OpenAI 格式的 tool definitions，供 chat completion 使用。"""
    return [
        {
            "type": "function",
            "function": {
                "name": "semantic_search",
                "description": "在指定知识库中按语义相似度搜索与问题最相关的文档片段。适合概念性、自然语言问题。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索问题或关键词"},
                        "top_k": {"type": "integer", "description": "返回条数", "default": 10},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "keyword_search",
                "description": "在知识库中按关键词匹配搜索，适合精确词、专有名词。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "关键词或短语"},
                        "top_k": {"type": "integer", "description": "返回条数", "default": 10},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "hybrid_search",
                "description": "混合搜索：结合语义与关键词，适合既要概念又要精确匹配的查询。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索内容"},
                        "top_k": {"type": "integer", "description": "返回条数", "default": 10},
                    },
                    "required": ["query"],
                },
            },
        },
    ]


def execute_tool(kb_id: int, name: str, arguments: dict) -> list[dict]:
    """根据工具名和参数执行检索，返回检索结果列表。"""
    query = (arguments.get("query") or "").strip()
    top_k = int(arguments.get("top_k") or 10)
    top_k = min(max(top_k, 1), 50)
    if name == "semantic_search":
        return semantic_search(kb_id, query, top_k=top_k)
    if name == "keyword_search":
        return keyword_search(kb_id, query, top_k=top_k)
    if name == "hybrid_search":
        return hybrid_search(kb_id, query, top_k=top_k)
    return []
