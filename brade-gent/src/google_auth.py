import secrets
import sqlite3
from datetime import datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from src import db
from src.config import Settings

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _client_config(settings: Settings) -> dict[str, Any]:
    return {
        "web": {
            "client_id": settings.google_client_id,
            "project_id": settings.google_project_id,
            "auth_uri": settings.google_auth_uri,
            "token_uri": settings.google_token_uri,
            "client_secret": settings.google_client_secret,
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def create_google_auth_url(
    settings: Settings, conn: sqlite3.Connection, discord_user_id: int
) -> str:
    flow = Flow.from_client_config(_client_config(settings), scopes=SCOPES)
    flow.redirect_uri = settings.google_redirect_uri

    state = secrets.token_urlsafe(24)
    db.save_oauth_state(conn, state, discord_user_id)

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return auth_url


def exchange_code_for_tokens(
    settings: Settings, conn: sqlite3.Connection, state: str, code: str
) -> int:
    discord_user_id = db.pop_oauth_state(conn, state)
    if discord_user_id is None:
        raise ValueError("Invalid or expired OAuth state.")

    flow = Flow.from_client_config(_client_config(settings), scopes=SCOPES, state=state)
    flow.redirect_uri = settings.google_redirect_uri
    flow.fetch_token(code=code)
    creds = flow.credentials

    expiry_iso = creds.expiry.isoformat() if creds.expiry else None
    db.save_google_tokens(
        conn,
        discord_user_id=discord_user_id,
        access_token=creds.token,
        refresh_token=creds.refresh_token,
        expiry_iso=expiry_iso,
    )
    return discord_user_id


def get_user_credentials(
    settings: Settings, conn: sqlite3.Connection, discord_user_id: int
) -> Credentials:
    user = db.get_user(conn, discord_user_id)
    if not user or not user["google_refresh_token"]:
        raise RuntimeError("Google Calendar is not connected. Use !connect first.")

    expiry = None
    if user["google_token_expiry"]:
        expiry = datetime.fromisoformat(user["google_token_expiry"])

    creds = Credentials(
        token=user["google_access_token"],
        refresh_token=user["google_refresh_token"],
        token_uri=settings.google_token_uri,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
        expiry=expiry,
    )

    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        db.save_google_tokens(
            conn,
            discord_user_id=discord_user_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            expiry_iso=creds.expiry.isoformat() if creds.expiry else None,
        )

    return creds
