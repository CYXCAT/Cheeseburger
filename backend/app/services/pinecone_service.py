"""Pinecone 向量库服务：创建索引（内置 embed）、upsert、语义/关键词/混合搜索、删除。
参考 pinecone-doc：create_index_for_model、upsert_records、search_records、delete。
"""
from __future__ import annotations

import time
from typing import Any

from app.core.config import settings


def _namespace(kb_id: int) -> str:
    return f"kb_{kb_id}"


class PineconeService:
    """单例 Pinecone 服务：一个共享 index（integrated embedding），按 namespace 隔离各知识库。"""

    _pc = None
    _index_name: str | None = None
    _index_host: str | None = None

    @classmethod
    def _client(cls):
        if cls._pc is None:
            if not settings.pinecone_api_key:
                raise RuntimeError("PINECONE_API_KEY is not set")
            from pinecone import Pinecone
            cls._pc = Pinecone(api_key=settings.pinecone_api_key)
        return cls._pc

    @classmethod
    def _ensure_index(cls) -> str:
        """确保全局 index 存在（create_index_for_model），返回 index host。"""
        name = settings.pinecone_index_name_prefix
        if cls._index_host:
            return cls._index_host
        pc = cls._client()
        if not pc.has_index(name):
            pc.create_index_for_model(
                name=name,
                cloud=settings.pinecone_cloud,
                region=settings.pinecone_region,
                embed={
                    "model": settings.pinecone_embed_model,
                    "field_map": {"text": "chunk_text"},
                },
            )
            time.sleep(2)
        desc = pc.describe_index(name)
        cls._index_name = name
        cls._index_host = desc.get("host") if isinstance(desc, dict) else getattr(desc, "host", None)
        if not cls._index_host:
            raise RuntimeError(f"Could not get host for index {name}")
        return cls._index_host

    @classmethod
    def _index(cls):
        host = cls._ensure_index()
        return cls._client().Index(host=host)

    # Pinecone 单次 upsert 批次上限
    _UPSERT_BATCH_SIZE = 96

    @classmethod
    def upsert_records(cls, kb_id: int, records: list[dict[str, Any]]) -> None:
        """将多条 record（含 chunk_text）写入该知识库 namespace，按批（≤96）发送。"""
        if not records:
            return
        ns = _namespace(kb_id)
        idx = cls._index()
        for i in range(0, len(records), cls._UPSERT_BATCH_SIZE):
            batch = records[i : i + cls._UPSERT_BATCH_SIZE]
            idx.upsert_records(ns, batch)
            time.sleep(0.3)

    @classmethod
    def search_semantic(
        cls,
        kb_id: int,
        query_text: str,
        top_k: int = 10,
        filter_expr: dict | None = None,
        fields: list[str] | None = None,
    ) -> list[dict]:
        """语义搜索：用 query 文本在 namespace 内检索（内置 text→vector）。"""
        ns = _namespace(kb_id)
        idx = cls._index()
        params = {
            "namespace": ns,
            "query": {"inputs": {"text": query_text}, "top_k": top_k},
            "fields": fields if fields is not None else ["chunk_text", "source_id"],
        }
        if filter_expr is not None:
            params["query"]["filter"] = filter_expr
        resp = idx.search(**params)
        return _normalize_search_response(resp)

    @classmethod
    def search_keyword(
        cls,
        kb_id: int,
        query_text: str,
        top_k: int = 20,
        fields: list[str] | None = None,
    ) -> list[dict]:
        """关键词搜索：同一套 index 用文本做 search（Pinecone 集成 embed 仍会做向量检索），
        再在应用层按关键词过滤 chunk_text，实现关键词命中。
        """
        raw = cls.search_semantic(kb_id, query_text, top_k=top_k * 2, fields=fields or ["chunk_text", "source_id"])
        q_lower = query_text.lower()
        keywords = [w.strip() for w in q_lower.split() if len(w.strip()) > 1]
        out = []
        for r in raw:
            text = (r.get("chunk_text") or r.get("metadata", {}).get("chunk_text") or "")
            if not keywords or any(k in text.lower() for k in keywords):
                out.append(r)
            if len(out) >= top_k:
                break
        return out[:top_k]

    @classmethod
    def search_hybrid(
        cls,
        kb_id: int,
        query_text: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        fields: list[str] | None = None,
    ) -> list[dict]:
        """混合搜索：语义 + 关键词结果合并去重，按综合得分排序。"""
        sem = cls.search_semantic(kb_id, query_text, top_k=top_k * 2, fields=fields)
        kw = cls.search_keyword(kb_id, query_text, top_k=top_k * 2, fields=fields)
        seen = set()
        scored = []
        for i, r in enumerate(sem):
            rid = r.get("id") or r.get("_id") or id(r)
            if rid not in seen:
                seen.add(rid)
                score = (1 - semantic_weight) * (1.0 - i / max(len(sem), 1))
                scored.append((r, semantic_weight * (r.get("score") or 0) + score))
        for i, r in enumerate(kw):
            rid = r.get("id") or r.get("_id") or id(r)
            if rid not in seen:
                seen.add(rid)
                score = semantic_weight * 0.5 + (1 - semantic_weight) * (1.0 - i / max(len(kw), 1))
                scored.append((r, score))
        scored.sort(key=lambda x: -x[1])
        return [r for r, _ in scored[:top_k]]

    @classmethod
    def delete_by_ids(cls, kb_id: int, record_ids: list[str]) -> None:
        """按 record id 删除。"""
        if not record_ids:
            return
        idx = cls._index()
        idx.delete(ids=record_ids, namespace=_namespace(kb_id))

    @classmethod
    def delete_by_source_id(cls, kb_id: int, source_id: str) -> None:
        """删除该知识库下某文档（source_id）的全部 chunk。"""
        idx = cls._index()
        idx.delete(
            filter={"source_id": {"$eq": source_id}},
            namespace=_namespace(kb_id),
        )

    @classmethod
    def delete_namespace(cls, kb_id: int) -> None:
        """清空该知识库 namespace 下所有记录。"""
        idx = cls._index()
        idx.delete(delete_all=True, namespace=_namespace(kb_id))

    @classmethod
    def get_namespace_stats(cls, kb_id: int) -> dict[str, Any]:
        """查询该知识库 namespace 在 Pinecone 中的记录数，用于验证是否有数据。"""
        ns = _namespace(kb_id)
        idx = cls._index()
        try:
            stats = idx.describe_index_stats()
        except Exception as e:
            return {"namespace": ns, "error": str(e), "record_count": None}
        namespaces = getattr(stats, "namespaces", None) or (stats.get("namespaces") if isinstance(stats, dict) else None)
        if namespaces is None:
            return {"namespace": ns, "record_count": 0, "note": "no namespaces in stats"}
        ns_info = namespaces.get(ns) if isinstance(namespaces, dict) else None
        if ns_info is None:
            return {"namespace": ns, "record_count": 0, "note": "namespace not found (no data yet)"}
        count = getattr(ns_info, "vector_count", None) or (ns_info.get("vector_count") if isinstance(ns_info, dict) else ns_info.get("record_count"))
        return {"namespace": ns, "record_count": count or 0}


def _normalize_search_response(resp: Any) -> list[dict]:
    """将 Pinecone search 响应转为统一 list[dict]，含 id、score、chunk_text、metadata。"""
    out = []
    # 兼容 result.hits（text search）与 matches（vector search）
    hits = getattr(getattr(resp, "result", None), "hits", None)
    if hits is not None:
        for m in hits:
            fields = getattr(m, "fields", None) or {}
            if not isinstance(fields, dict):
                fields = dict(fields) if hasattr(fields, "items") else {}
            d = {
                "id": getattr(m, "_id", None) or getattr(m, "id", None),
                "score": getattr(m, "_score", None) or getattr(m, "score", None),
                "chunk_text": fields.get("chunk_text") if isinstance(fields, dict) else getattr(m, "chunk_text", None),
                "metadata": fields,
            }
            out.append(d)
        return out
    matches = getattr(resp, "matches", resp) if not isinstance(resp, list) else resp
    if hasattr(matches, "__iter__") and not isinstance(matches, dict):
        for m in matches:
            d = {"id": getattr(m, "id", None) or getattr(m, "_id", None)}
            if hasattr(m, "score"):
                d["score"] = m.score
            if hasattr(m, "metadata"):
                d["metadata"] = dict(m.metadata) if m.metadata else {}
            if hasattr(m, "chunk_text"):
                d["chunk_text"] = m.chunk_text
            elif hasattr(m, "fields") and m.fields:
                f = m.fields if isinstance(m.fields, dict) else getattr(m.fields, "__dict__", {})
                d["chunk_text"] = f.get("chunk_text")
            elif d.get("metadata") and "chunk_text" in d["metadata"]:
                d["chunk_text"] = d["metadata"]["chunk_text"]
            out.append(d)
    return out
