from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "photo-organizer"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/photo_organizer"

    REDIS_URL: str = "redis://redis:6379/0"

    # SMS (Aliyun SMS)
    SMS_ACCESS_KEY_ID: str = ""
    SMS_ACCESS_KEY_SECRET: str = ""
    SMS_SIGN_NAME: str = ""
    SMS_TEMPLATE_CODE: str = ""

    # SMS verification code
    SMS_CODE_LENGTH: int = 6
    SMS_CODE_EXPIRE_SECONDS: int = 300  # 5 minutes
    SMS_RATE_LIMIT_SECONDS: int = 60  # 1 per minute per phone

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    ENCRYPTION_KEY: str = "change-me-to-a-32-byte-hex-string"

    STORAGE_ENDPOINT: str = "http://minio:9000"
    STORAGE_PUBLIC_URL: str = ""  # Public-facing URL for browser access, e.g. http://localhost:29000
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET: str = "photo-organizer"
    STORAGE_REGION: str = "ap-guangzhou"

    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_PIXELS: int = 100_000_000  # 100MP
    THUMBNAIL_SIZE: int = 300
    COMPRESSED_SIZE: int = 1200

    CORS_ORIGINS: str = "*"  # comma-separated list or "*"

    model_config = {"env_file": ".env", "case_sensitive": True}

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        if self.APP_ENV == "production":
            insecure = {"change-me", "change-me-to-a-32-byte-hex-string"}
            if self.JWT_SECRET_KEY in insecure:
                raise ValueError("JWT_SECRET_KEY must be set in production")
            if self.ENCRYPTION_KEY in insecure:
                raise ValueError("ENCRYPTION_KEY must be set in production")
            if self.SECRET_KEY in insecure:
                raise ValueError("SECRET_KEY must be set in production")
        return self


settings = Settings()
