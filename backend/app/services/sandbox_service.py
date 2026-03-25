"""Daytona 沙盒服务：创建沙盒、执行代码、返回结果。"""
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# 默认执行超时（秒）
DEFAULT_TIMEOUT = 30


def execute(code: str, language: str = "python") -> dict[str, Any]:
    """
    在 Daytona 沙盒中执行代码，返回统一结构。
    :param code: 要执行的代码
    :param language: 语言，如 python, javascript 等
    :return: {"code": str, "language": str, "exit_code": int, "result": str}
    """
    if not settings.daytona_api_key:
        return {
            "code": code,
            "language": language,
            "exit_code": -1,
            "result": "Daytona 未配置（DAYTONA_API_KEY），无法执行代码。",
        }
    try:
        from daytona import Daytona, DaytonaConfig

        config = DaytonaConfig(api_key=settings.daytona_api_key)
        daytona = Daytona(config)
        sandbox = daytona.create()
        try:
            response = sandbox.process.code_run(code, timeout=DEFAULT_TIMEOUT)
            exit_code = getattr(response, "exit_code", -1)
            result = getattr(response, "result", "") or ""
            return {
                "code": code,
                "language": language,
                "exit_code": int(exit_code),
                "result": str(result).strip(),
            }
        finally:
            try:
                daytona.delete(sandbox)
            except Exception as e:
                logger.warning("sandbox delete: %s", e)
    except ImportError as e:
        logger.exception("daytona sdk not available: %s", e)
        return {
            "code": code,
            "language": language,
            "exit_code": -1,
            "result": f"沙盒依赖未安装或不可用: {e!s}",
        }
    except Exception as e:
        logger.exception("sandbox execute error: %s", e)
        return {
            "code": code,
            "language": language,
            "exit_code": -1,
            "result": f"执行失败: {e!s}",
        }
