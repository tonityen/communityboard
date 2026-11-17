import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY or SECRET_KEY == "change-this-secret-key":
        raise RuntimeError(
            "Set SECRET_KEY in the .env file to a long random value. "
            'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "communityboard")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes"}
    
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MUNICIPALITY_EMAIL = os.getenv("MUNICIPALITY_EMAIL", "")
    ADMIN_ACCESS_CODE = os.getenv("ADMIN_ACCESS_CODE", "")
