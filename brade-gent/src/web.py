from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from src import db
from src.config import load_settings
from src.google_auth import exchange_code_for_tokens

settings = load_settings()
conn = db.connect(settings.db_path)
db.init_db(conn)
app = FastAPI()


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/oauth/google/callback")
async def google_callback(
    state: str = Query(...),
    code: str = Query(...),
):
    try:
        discord_user_id = exchange_code_for_tokens(settings, conn, state=state, code=code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OAuth exchange failed: {exc}") from exc

    return HTMLResponse(
        content=(
            "<h2>Google Calendar connected.</h2>"
            f"<p>Discord user ID: {discord_user_id}</p>"
            "<p>You can return to Discord and run <code>!today</code>.</p>"
        )
    )
