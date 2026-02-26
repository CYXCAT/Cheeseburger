from fastapi import APIRouter
from . import kb, documents, llm, chat_history

api_router = APIRouter(prefix="/api")
api_router.include_router(kb.router, prefix="/knowledge-bases", tags=["knowledge-bases"])
api_router.include_router(documents.router, prefix="/knowledge-bases", tags=["documents"])
api_router.include_router(chat_history.router, prefix="/knowledge-bases", tags=["chat-history"])
api_router.include_router(llm.router, prefix="/chat", tags=["llm"])
