"""文档上传（PDF/URL/纯文本）、删除、语义/关键词/混合搜索。"""
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.repositories import KBRepository
from app.services.parsers import parse_document
from app.services.pinecone_service import PineconeService
from app.api.schemas import DocumentUploadResponse, DocumentOut, SearchRequest, SearchResult, SearchResponse

router = APIRouter()


async def _get_kb_or_404(kb_id: int, user_id: str, db: AsyncSession):
    repo = KBRepository(db)
    kb = await repo.get_kb(kb_id, user_id)
    if not kb:
        raise HTTPException(404, "Knowledge base not found")
    return kb


@router.get("/{kb_id}/documents/pinecone-stats")
async def pinecone_stats(
    kb_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """验证该知识库在 Pinecone 中是否有数据（仅用于调试）。"""
    await _get_kb_or_404(kb_id, user_id, db)
    return PineconeService.get_namespace_stats(kb_id)


@router.get("/{kb_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    kb_id: int,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    repo = KBRepository(db)
    return await repo.list_documents(kb_id)


@router.post("/{kb_id}/documents/upload-pdf", response_model=DocumentUploadResponse)
async def upload_pdf(
    kb_id: int,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")
    raw = await file.read()
    source_id = f"pdf_{uuid.uuid4().hex[:12]}"
    chunks = parse_document(raw, source_id, "pdf")
    records = [c.to_record(f"{source_id}_{c.chunk_index}") for c in chunks]
    PineconeService.upsert_records(kb_id, records)
    repo = KBRepository(db)
    await repo.add_document(kb_id, source_id, "pdf", len(records))
    return DocumentUploadResponse(kb_id=kb_id, source_id=source_id, source_type="pdf", chunks_count=len(records))


@router.post("/{kb_id}/documents/upload-url", response_model=DocumentUploadResponse)
async def upload_url(
    kb_id: int,
    url: str = Form(..., min_length=1),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    source_id = f"url_{uuid.uuid4().hex[:12]}"
    chunks = parse_document(url.strip(), source_id, "url")
    records = [c.to_record(f"{source_id}_{c.chunk_index}") for c in chunks]
    PineconeService.upsert_records(kb_id, records)
    repo = KBRepository(db)
    await repo.add_document(kb_id, source_id, "url", len(records))
    return DocumentUploadResponse(kb_id=kb_id, source_id=source_id, source_type="url", chunks_count=len(records))


@router.post("/{kb_id}/documents/upload-text", response_model=DocumentUploadResponse)
async def upload_text(
    kb_id: int,
    text: str = Form(..., min_length=1),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    source_id = f"text_{uuid.uuid4().hex[:12]}"
    chunks = parse_document(text, source_id, "text")
    records = [c.to_record(f"{source_id}_{c.chunk_index}") for c in chunks]
    PineconeService.upsert_records(kb_id, records)
    repo = KBRepository(db)
    await repo.add_document(kb_id, source_id, "text", len(records))
    return DocumentUploadResponse(kb_id=kb_id, source_id=source_id, source_type="text", chunks_count=len(records))


@router.delete("/{kb_id}/documents/{source_id}", status_code=204)
async def delete_document(
    kb_id: int,
    source_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    PineconeService.delete_by_source_id(kb_id, source_id)
    repo = KBRepository(db)
    await repo.delete_document_record(kb_id, source_id)


@router.post("/{kb_id}/search", response_model=SearchResponse)
async def search(
    kb_id: int,
    body: SearchRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_kb_or_404(kb_id, user_id, db)
    st = (body.search_type or "semantic").lower()
    if st == "semantic":
        raw = PineconeService.search_semantic(kb_id, body.query, top_k=body.top_k)
    elif st == "keyword":
        raw = PineconeService.search_keyword(kb_id, body.query, top_k=body.top_k)
    elif st == "hybrid":
        raw = PineconeService.search_hybrid(kb_id, body.query, top_k=body.top_k)
    else:
        raw = PineconeService.search_semantic(kb_id, body.query, top_k=body.top_k)
    results = [
        SearchResult(
            id=r.get("id"),
            score=r.get("score"),
            chunk_text=r.get("chunk_text") or (r.get("metadata") or {}).get("chunk_text"),
            metadata=r.get("metadata"),
        )
        for r in raw
    ]
    return SearchResponse(results=results)
