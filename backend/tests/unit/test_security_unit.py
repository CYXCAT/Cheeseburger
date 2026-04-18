"""security：密码哈希与 JWT 编解码（依赖 conftest 中的 JWT_SECRET）。"""
from __future__ import annotations

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


@pytest.mark.unit
def test_hash_and_verify_round_trip():
    h = hash_password("secret-pass")
    assert verify_password("secret-pass", h) is True
    assert verify_password("wrong", h) is False


@pytest.mark.unit
def test_access_token_round_trip():
    token = create_access_token("user-42")
    assert decode_access_token(token) == "user-42"


@pytest.mark.unit
def test_decode_invalid_token_returns_none():
    assert decode_access_token("not.a.jwt") is None
    assert decode_access_token("") is None
