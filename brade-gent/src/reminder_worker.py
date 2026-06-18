import asyncio
from datetime import datetime, timedelta, timezone

from src import calendar_service, db
from src.config import load_settings
from src.discord_rest import send_dm


def _event_start_utc(event: dict) -> datetime | None:
    start = event.get("start", {})
    dt = start.get("dateTime")
    if not dt:
        return None
    parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc)


def _parse_minutes_csv(value: str | None) -> list[int]:
    if not value:
        return [30, 5]
    out = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out or [30, 5]


async def run_worker() -> None:
    settings = load_settings()
    conn = db.connect(settings.db_path)
    db.init_db(conn)

    while True:
        now = datetime.now(tz=timezone.utc)
        window_end = now + timedelta(hours=3)

        users = db.list_connected_users(conn)
        for user in users:
            discord_user_id = int(user["discord_user_id"])
            try:
                events = calendar_service.list_events_window(
                    settings, conn, discord_user_id, now, window_end
                )
            except Exception as exc:
                print(f"[worker] calendar fetch failed for {discord_user_id}: {exc}")
                continue

            reminder_minutes = _parse_minutes_csv(user["reminder_minutes"])
            for event in events:
                event_id = event.get("id")
                start_utc = _event_start_utc(event)
                if not event_id or not start_utc:
                    continue

                for minutes in reminder_minutes:
                    remind_at = start_utc - timedelta(minutes=minutes)
                    is_due = remind_at <= now < (remind_at + timedelta(seconds=settings.reminder_poll_seconds + 5))
                    remind_at_iso = remind_at.isoformat()
                    if not is_due:
                        continue
                    if db.reminder_already_sent(conn, discord_user_id, event_id, remind_at_iso):
                        continue

                    summary = event.get("summary", "(No title)")
                    start_value = event.get("start", {}).get("dateTime", event.get("start", {}).get("date"))
                    msg = (
                        f"Reminder: `{summary}` starts in {minutes} minutes.\n"
                        f"Start: {start_value}\n"
                        f"Event ID: `{event_id}`"
                    )
                    try:
                        await send_dm(settings.discord_bot_token, discord_user_id, msg)
                        db.mark_reminder_sent(conn, discord_user_id, event_id, remind_at_iso)
                    except Exception as exc:
                        print(f"[worker] DM failed for {discord_user_id}: {exc}")

        await asyncio.sleep(settings.reminder_poll_seconds)


if __name__ == "__main__":
    asyncio.run(run_worker())
