import os
from pydantic import BaseModel

class Settings(BaseModel):
    TELEGRAM_BOT_TOKEN: str
    DATABASE_URL: str = "sqlite+aiosqlite:///./bankroll.db"
    TZ: str = os.getenv("TZ", "Europe/Moscow")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def load(cls) -> "Settings":
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
        return cls(
            TELEGRAM_BOT_TOKEN=token,
            DATABASE_URL=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bankroll.db"),
        )
