import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestConfigValidation:
    def test_development_allows_default_secrets(self):
        # Force default values regardless of .env
        s = Settings(APP_ENV="development", JWT_SECRET_KEY="change-me", _env_file=None)
        assert s.JWT_SECRET_KEY == "change-me"

    def test_production_rejects_default_jwt_secret(self):
        with pytest.raises((ValidationError, ValueError)):
            Settings(APP_ENV="production", JWT_SECRET_KEY="change-me")

    def test_production_rejects_default_encryption_key(self):
        with pytest.raises((ValidationError, ValueError)):
            Settings(
                APP_ENV="production",
                JWT_SECRET_KEY="secure-jwt-key-for-testing-only",
                ENCRYPTION_KEY="change-me-to-a-32-byte-hex-string",
            )

    def test_production_accepts_valid_secrets(self):
        s = Settings(
            APP_ENV="production",
            JWT_SECRET_KEY="secure-jwt-key-for-testing-only",
            ENCRYPTION_KEY="a" * 64,
            SECRET_KEY="secure-secret-key",
        )
        assert s.APP_ENV == "production"

    def test_cors_origins_default_is_wildcard(self):
        s = Settings()
        assert s.CORS_ORIGINS == "*"

    def test_cors_origins_can_be_set(self):
        s = Settings(CORS_ORIGINS="https://example.com,https://app.example.com")
        assert "https://example.com" in s.CORS_ORIGINS
