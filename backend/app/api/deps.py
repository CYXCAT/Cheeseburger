"""公共依赖：从 JWT 解析当前用户。"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token

security = HTTPBearer(auto_error=False)


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
