"""应用配置，从环境变量读取。"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    app_name: str = "doc-kb-api"
    debug: bool = False

    # 数据库（默认 SQLite；设 DATABASE_URL 为 Supabase 连接串即切到 Postgres）
    database_url: str = "sqlite+aiosqlite:///./app.db"

    # Pinecone（参考 pinecone-doc）
    pinecone_api_key: str = ""
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    pinecone_embed_model: str = "llama-text-embed-v2"
    pinecone_index_name_prefix: str = "doc-kb"

    # LLM（OpenAI 兼容）
    openai_api_key: str = ""
    openai_base_url: str | None = None  # 可指向本地或第三方
    llm_model: str = "gpt-4o-mini"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # 邀请链接前端 base（仅用于 scripts/generate_invites.py 打印完整链接）
    invite_base_url: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
