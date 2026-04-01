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

    # Billing（按 tokens 计费，预付费钱包）
    billing_enabled: bool = True
    billing_currency: str = "USD"
    # 以“每 1k tokens 的价格（分）”计价；可用环境变量覆盖（JSON 字典）
    # 示例：{"gpt-4o-mini": 3, "gpt-4.1-mini": 10}
    model_prices_cents_per_1k: dict[str, int] = {"gpt-4o-mini": 3}
    # 用于在余额不足时限制 completion 上限（prompt tokens 仍会消耗）
    billing_max_completion_tokens: int = 512
    # 允许手工充值的管理员用户 ID（逗号分隔，例如 "1,2,3"）；空则仅 debug 模式允许
    admin_user_ids: str = ""

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # 邀请链接前端 base（仅用于 scripts/generate_invites.py 打印完整链接）
    invite_base_url: str = ""

    # Daytona 沙盒（代码执行）
    daytona_api_key: str = ""

    # Planner / 编排（Plan-and-Execute）
    planner_max_steps: int = 6
    code_max_sandbox_retries: int = 2  # 沙箱非零退出后，除首次外最多再试次数
    orchestration_max_replan: int = 2
    # 编排 while 最大迭代次数（含再规划插入的新步），防止异常路径死循环
    orchestration_max_loop_iterations: int = 48
    planner_max_completion_tokens: int = 1024
    # 为 True 或 debug=True 时开放 POST /api/chat/planner-debug（仅本地/排障，生产请关）
    planner_debug_enabled: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
