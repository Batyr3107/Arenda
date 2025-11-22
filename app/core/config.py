from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Arenda - Property Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 5
    ENABLE_2FA: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    ENABLE_REQUEST_LOGGING: bool = True
    SENTRY_DSN: str = None

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False

    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "./uploads"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Telegram Bot (optional)
    TELEGRAM_BOT_TOKEN: str = None

    # SMS Service (optional)
    SMS_PROVIDER: str = "twilio"  # twilio, kaspi, custom
    TWILIO_ACCOUNT_SID: str = None
    TWILIO_AUTH_TOKEN: str = None
    TWILIO_PHONE_NUMBER: str = None
    KASPI_SMS_API_KEY: str = None
    KASPI_SMS_API_URL: str = None

    # Payment Gateways (optional)
    STRIPE_API_KEY: str = None
    STRIPE_WEBHOOK_SECRET: str = None
    KASPI_PAYMENT_API_KEY: str = None
    KASPI_PAYMENT_MERCHANT_ID: str = None
    ENABLE_ONLINE_PAYMENTS: bool = False

    # File Storage (optional)
    STORAGE_PROVIDER: str = "local"  # local, s3, azure
    AWS_ACCESS_KEY_ID: str = None
    AWS_SECRET_ACCESS_KEY: str = None
    AWS_S3_BUCKET: str = None
    AWS_S3_REGION: str = "us-east-1"

    # Monitoring (optional)
    ENABLE_METRICS: bool = False
    PROMETHEUS_PORT: int = 9090

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
