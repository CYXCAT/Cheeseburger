"""公共依赖：从 JWT 解析当前用户、是否管理员。"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import decode_access_token

security = HTTPBearer(auto_error=False)


def is_admin(user_id: int) -> bool:
    if settings.debug:
        return True
    raw = (settings.admin_user_ids or "").strip()
    if not raw:
        return False
    allowed = {s.strip() for s in raw.split(",") if s.strip()}
    return str(user_id) in allowed


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Missing or invalid authorization")
    token = credentials.credentials
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(401, "Invalid or expired token")
    return user_id
