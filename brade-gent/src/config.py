import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    discord_bot_token: str
    allowed_discord_user_id: int
    openai_api_key: str
    openai_model: str
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str
    google_project_id: str
    google_auth_uri: str
    google_token_uri: str
    db_path: str
    bot_public_base_url: str
    reminder_poll_seconds: int
    default_timezone: str


def load_settings() -> Settings:
    return Settings(
        discord_bot_token=_required("DISCORD_BOT_TOKEN"),
        allowed_discord_user_id=int(_required("ALLOWED_DISCORD_USER_ID")),
        openai_api_key=_required("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        google_client_id=_required("GOOGLE_CLIENT_ID"),
        google_client_secret=_required("GOOGLE_CLIENT_SECRET"),
        google_redirect_uri=_required("GOOGLE_REDIRECT_URI"),
        google_project_id=os.getenv("GOOGLE_PROJECT_ID", "discord-calendar-agent"),
        google_auth_uri=os.getenv(
            "GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"
        ),
        google_token_uri=os.getenv(
            "GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token"
        ),
        db_path=os.getenv("DB_PATH", "./data/app.db"),
        bot_public_base_url=_required("BOT_PUBLIC_BASE_URL"),
        reminder_poll_seconds=int(os.getenv("REMINDER_POLL_SECONDS", "60")),
        default_timezone=os.getenv("DEFAULT_TIMEZONE", "America/New_York"),
    )
