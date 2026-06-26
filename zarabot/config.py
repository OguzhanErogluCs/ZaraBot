from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    poll_interval_seconds: int
    database_path: Path


def load_settings(database_override: str | None = None, interval_override: int | None = None) -> Settings:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    interval = interval_override or int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
    database_path = Path(database_override or os.getenv("DATABASE_PATH", "data/zarabot.sqlite3"))

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required. Add it to .env.")
    if not chat_id:
        raise ValueError("TELEGRAM_CHAT_ID is required. Add it to .env.")
    if interval < 30:
        raise ValueError("POLL_INTERVAL_SECONDS must be at least 30 seconds.")

    return Settings(
        telegram_bot_token=token,
        telegram_chat_id=chat_id,
        poll_interval_seconds=interval,
        database_path=database_path,
    )
