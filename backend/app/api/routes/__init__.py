from fastapi import APIRouter
from . import admin, auth, billing, chat_history, documents, kb, llm, usage, users

api_router = APIRouter(prefix="/api")
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(kb.router, prefix="/knowledge-bases", tags=["knowledge-bases"])
api_router.include_router(documents.router, prefix="/knowledge-bases", tags=["documents"])
api_router.include_router(chat_history.router, prefix="/knowledge-bases", tags=["chat-history"])
api_router.include_router(llm.router, prefix="/chat", tags=["llm"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
