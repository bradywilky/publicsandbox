import asyncio
from datetime import datetime

import discord
from discord.ext import commands

from src import calendar_service, db
from src.agent import parse_calendar_intent
from src.config import load_settings
from src.google_auth import create_google_auth_url


def _fmt_event_line(event: dict) -> str:
    start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
    summary = event.get("summary", "(No title)")
    event_id = event.get("id", "")
    return f"- `{event_id}` | {start} | {summary}"


def create_bot() -> commands.Bot:
    settings = load_settings()
    conn = db.connect(settings.db_path)
    db.init_db(conn)

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

    def is_allowed(ctx: commands.Context) -> bool:
        return ctx.author.id == settings.allowed_discord_user_id

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user} (id={bot.user.id})")

    @bot.command()
    async def help(ctx: commands.Context):
        if not is_allowed(ctx):
            return
        await ctx.send(
            "\n".join(
                [
                    "Commands:",
                    "`!connect` - Link Google Calendar",
                    "`!today` - List today's events",
                    "`!create \"Title\" 2026-04-16T14:00:00-04:00 2026-04-16T14:30:00-04:00`",
                    "`!move <event_id> <new_start_iso> <new_end_iso>`",
                    "`!delete <event_id>`",
                    "`!reminders 30,5` - minutes before events",
                    "`!agent <text>` - natural language request",
                ]
            )
        )

    @bot.command()
    async def connect(ctx: commands.Context):
        if not is_allowed(ctx):
            return
        db.upsert_user_if_missing(conn, ctx.author.id)
        auth_url = create_google_auth_url(settings, conn, ctx.author.id)
        await ctx.send(
            "Open this URL to connect Google Calendar, then approve access:\n"
            f"{auth_url}"
        )

    @bot.command()
    async def today(ctx: commands.Context):
        if not is_allowed(ctx):
            return
        try:
            events = calendar_service.list_events_for_today(settings, conn, ctx.author.id)
        except Exception as exc:
            await ctx.send(f"Could not fetch calendar: {exc}")
            return
        if not events:
            await ctx.send("No events found for today.")
            return
        lines = ["Today's events:"] + [_fmt_event_line(e) for e in events[:20]]
        await ctx.send("\n".join(lines))

    @bot.command()
    async def create(ctx: commands.Context, title: str, start_iso: str, end_iso: str):
        if not is_allowed(ctx):
            return
        try:
            user = db.get_user(conn, ctx.author.id)
            tz_name = user["timezone"] if user and user["timezone"] else settings.default_timezone
            event = calendar_service.create_event(
                settings, conn, ctx.author.id, title, start_iso, end_iso, tz_name
            )
            await ctx.send(
                f"Created event `{event.get('id')}`: {event.get('summary')} at {event.get('start', {}).get('dateTime')}"
            )
        except Exception as exc:
            await ctx.send(f"Create failed: {exc}")

    @bot.command()
    async def move(ctx: commands.Context, event_id: str, new_start_iso: str, new_end_iso: str):
        if not is_allowed(ctx):
            return
        try:
            user = db.get_user(conn, ctx.author.id)
            tz_name = user["timezone"] if user and user["timezone"] else settings.default_timezone
            event = calendar_service.move_event(
                settings,
                conn,
                ctx.author.id,
                event_id,
                new_start_iso,
                new_end_iso,
                tz_name,
            )
            await ctx.send(
                f"Moved `{event.get('id')}` to {event.get('start', {}).get('dateTime')}."
            )
        except Exception as exc:
            await ctx.send(f"Move failed: {exc}")

    @bot.command()
    async def delete(ctx: commands.Context, event_id: str):
        if not is_allowed(ctx):
            return
        try:
            calendar_service.delete_event(settings, conn, ctx.author.id, event_id)
            await ctx.send(f"Deleted event `{event_id}`.")
        except Exception as exc:
            await ctx.send(f"Delete failed: {exc}")

    @bot.command()
    async def reminders(ctx: commands.Context, minutes_csv: str):
        if not is_allowed(ctx):
            return
        db.update_reminder_minutes(conn, ctx.author.id, minutes_csv)
        await ctx.send(f"Updated reminder minutes to `{minutes_csv}`.")

    @bot.command()
    async def tz(ctx: commands.Context, timezone_name: str):
        if not is_allowed(ctx):
            return
        db.update_timezone(conn, ctx.author.id, timezone_name)
        await ctx.send(f"Timezone set to `{timezone_name}`.")

    @bot.command()
    async def agent(ctx: commands.Context, *, text: str):
        if not is_allowed(ctx):
            return
        user = db.get_user(conn, ctx.author.id)
        timezone_name = user["timezone"] if user and user["timezone"] else settings.default_timezone
        try:
            parsed = await asyncio.to_thread(
                parse_calendar_intent,
                settings.openai_api_key,
                settings.openai_model,
                text,
                timezone_name,
            )
        except Exception as exc:
            await ctx.send(f"Agent parse failed: {exc}")
            return

        intent = parsed.get("intent")
        if intent == "today":
            await today(ctx)
            return
        if intent == "create":
            if not parsed.get("summary") or not parsed.get("start_iso") or not parsed.get("end_iso"):
                await ctx.send(parsed.get("assistant_reply", "Need title/start/end."))
                return
            await create(ctx, parsed["summary"], parsed["start_iso"], parsed["end_iso"])
            return
        if intent == "move":
            if not parsed.get("event_id") or not parsed.get("start_iso") or not parsed.get("end_iso"):
                await ctx.send(parsed.get("assistant_reply", "Need event_id/start/end."))
                return
            await move(ctx, parsed["event_id"], parsed["start_iso"], parsed["end_iso"])
            return
        if intent == "delete":
            if parsed.get("needs_confirmation", True):
                await ctx.send(
                    "Delete request detected. Please confirm explicitly with `!delete <event_id>`."
                )
                return
            if not parsed.get("event_id"):
                await ctx.send(parsed.get("assistant_reply", "Need event_id to delete."))
                return
            await delete(ctx, parsed["event_id"])
            return

        await ctx.send(parsed.get("assistant_reply", "I could not confidently parse that request."))

    return bot


if __name__ == "__main__":
    app_bot = create_bot()
    app_bot.run(load_settings().discord_bot_token)
