from fastapi import APIRouter
from . import kb, documents, llm, chat_history, auth, users

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(kb.router, prefix="/knowledge-bases", tags=["knowledge-bases"])
api_router.include_router(documents.router, prefix="/knowledge-bases", tags=["documents"])
api_router.include_router(chat_history.router, prefix="/knowledge-bases", tags=["chat-history"])
api_router.include_router(llm.router, prefix="/chat", tags=["llm"])
