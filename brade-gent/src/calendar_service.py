from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from src.config import Settings
from src.google_auth import get_user_credentials


def _calendar_api(settings: Settings, conn, discord_user_id: int):
    creds = get_user_credentials(settings, conn, discord_user_id)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def list_events_for_today(settings: Settings, conn, discord_user_id: int) -> list[dict]:
    now = datetime.now(tz=timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    api = _calendar_api(settings, conn, discord_user_id)
    result = (
        api.events()
        .list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=50,
        )
        .execute()
    )
    return result.get("items", [])


def list_events_window(
    settings: Settings, conn, discord_user_id: int, start: datetime, end: datetime
) -> list[dict]:
    api = _calendar_api(settings, conn, discord_user_id)
    result = (
        api.events()
        .list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=200,
        )
        .execute()
    )
    return result.get("items", [])


def create_event(
    settings: Settings,
    conn,
    discord_user_id: int,
    summary: str,
    start_iso: str,
    end_iso: str,
    timezone_name: str,
) -> dict:
    api = _calendar_api(settings, conn, discord_user_id)
    body = {
        "summary": summary,
        "start": {"dateTime": start_iso, "timeZone": timezone_name},
        "end": {"dateTime": end_iso, "timeZone": timezone_name},
    }
    return api.events().insert(calendarId="primary", body=body).execute()


def move_event(
    settings: Settings,
    conn,
    discord_user_id: int,
    event_id: str,
    new_start_iso: str,
    new_end_iso: str,
    timezone_name: str,
) -> dict:
    api = _calendar_api(settings, conn, discord_user_id)
    event = api.events().get(calendarId="primary", eventId=event_id).execute()
    event["start"] = {"dateTime": new_start_iso, "timeZone": timezone_name}
    event["end"] = {"dateTime": new_end_iso, "timeZone": timezone_name}
    return api.events().update(calendarId="primary", eventId=event_id, body=event).execute()


def delete_event(settings: Settings, conn, discord_user_id: int, event_id: str) -> None:
    api = _calendar_api(settings, conn, discord_user_id)
    api.events().delete(calendarId="primary", eventId=event_id).execute()
