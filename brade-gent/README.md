# Discord Calendar Agent (Two-Way)

This starter project gives you:
- Two-way Discord chat with your private bot
- Google Calendar read/write access (OAuth)
- Background reminders sent to you via Discord DM
- 24/7-friendly deployment with Docker Compose (works well on EC2)

## 1) Create required credentials

### Discord
1. Create an app at https://discord.com/developers/applications
2. Create a bot and copy the bot token.
3. Enable `MESSAGE CONTENT INTENT` in Bot settings.
4. Invite bot to your private server (or use DM only).
5. Copy your Discord user ID (Developer Mode -> right-click your profile -> Copy User ID).

### Google Calendar OAuth
1. In Google Cloud Console, create project and enable Google Calendar API.
2. Create OAuth client credentials (`Web application`).
3. Add redirect URI:
   - `https://your-domain.com/oauth/google/callback` (production), or
   - `http://localhost:8000/oauth/google/callback` (local testing)
4. Copy Client ID and Client Secret.

## 2) Configure environment

1. Copy `.env.example` to `.env`
2. Fill all values.
3. Keep `ALLOWED_DISCORD_USER_ID` set to only your user ID for safety.

## 3) Run locally

```bash
docker compose up --build -d
```

Health check:

```bash
curl http://localhost:8000/health
```

## 4) Connect Google from Discord

In Discord DM with your bot:

```text
!connect
```

Open returned URL, approve Google consent, then test:

```text
!today
```

## 5) Discord commands

- `!help`
- `!connect`
- `!today`
- `!create "Title" 2026-04-16T14:00:00-04:00 2026-04-16T14:30:00-04:00`
- `!move <event_id> <new_start_iso> <new_end_iso>`
- `!delete <event_id>`
- `!reminders 30,5`
- `!tz America/New_York`
- `!agent move my 3pm meeting tomorrow to 4pm`

## 6) EC2 deployment notes

1. Launch Ubuntu EC2 instance.
2. Install Docker + Docker Compose plugin.
3. Open ports:
   - `22` SSH
   - `443` HTTPS (recommended)
   - `80` HTTP (for cert setup)
4. Clone repo, set `.env`, run `docker compose up -d --build`.
5. Put Nginx in front of `web` container and route `/oauth/google/callback`.
6. Use TLS cert (LetsEncrypt).
7. Update `GOOGLE_REDIRECT_URI` and Google OAuth redirect URI to your real HTTPS domain.

## Security recommendations

- Keep bot private and restricted to your Discord user ID.
- Store `.env` secrets securely (AWS SSM / Secrets Manager in production).
- Add KMS-backed token encryption before multi-user expansion.
- Add explicit confirmation flow for deletes if you expand beyond personal use.

## Architecture

- `src/discord_bot.py`: Discord command interface + agent handoff
- `src/web.py`: OAuth callback endpoint
- `src/reminder_worker.py`: periodic reminder sender
- `src/google_auth.py`: OAuth and token refresh
- `src/calendar_service.py`: calendar CRUD operations
- `src/db.py`: SQLite state and reminder tracking
