import pytest
from datetime import datetime, timezone

from app.core.security import create_access_token, decode_access_token


class TestSecurity:
    def test_create_and_decode_token(self):
        user_id = "test-user-123"
        token = create_access_token(user_id)
        payload = decode_access_token(token)
        assert payload["sub"] == user_id

    def test_token_contains_exp(self):
        token = create_access_token("user-1")
        payload = decode_access_token(token)
        assert "exp" in payload
        assert "iat" in payload

    def test_invalid_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid-token")
        assert exc_info.value.status_code == 401
