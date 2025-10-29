import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from app.utils.env_upsert import upsert_env_vars

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "dev-secret"))

CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
ALLOW_WRITE = os.environ.get("DEV_ALLOW_OAUTH_WRITE_DOTENV", "false").lower() == "true"

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    print("[oauth] Missing GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REDIRECT_URI in .env")

client_config = {
    "web": {
        "client_id": CLIENT_ID or "",
        "project_id": "spa",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": CLIENT_SECRET or "",
        "redirect_uris": [REDIRECT_URI or ""],
        "javascript_origins": [FRONTEND_ORIGIN],
    }
}


def make_flow() -> Flow:
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )


@app.get("/auth/google/login")
def google_login(request: Request):
    flow = make_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["state"] = state
    return RedirectResponse(auth_url)


@app.get("/auth/google/callback")
def google_callback(request: Request, state: str = "", code: str = ""):
    if state != request.session.get("state"):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    flow = make_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials

    refresh_token = getattr(creds, "refresh_token", None)

    if not refresh_token:
        html = """
        <h1>No refresh token received</h1>
        <p>Tip: Revoke the app in your Google Account (Security &rarr; Third-party access), then try again.<br/>
        Ensure 'prompt=consent' and 'access_type=offline' are set.</p>
        """
        return HTMLResponse(html)

    if not ALLOW_WRITE:
        return HTMLResponse(
            f"<h1>Refresh token obtained (dev-write disabled)</h1>"
            f"<p>DEV_ALLOW_OAUTH_WRITE_DOTENV is false. Not writing to .env.</p>"
            f"<p>Last 6 chars: <code>{refresh_token[-6:]}</code></p>"
        )

    upsert_env_vars({"GOOGLE_REFRESH_TOKEN": refresh_token})

    return HTMLResponse(
        f"<h1>Refresh token saved to .env</h1>"
        f"<p>Key: GOOGLE_REFRESH_TOKEN (masked) &bull; Last 6 chars: <code>{refresh_token[-6:]}</code></p>"
    )


@app.get("/health")
def health():
    return JSONResponse({"ok": True})
