#!/usr/bin/env python3
"""
Google OAuth Setup Script - Manual Mode
No redirect URI needed - you'll copy/paste the authorization code
"""
import os
import sys
from pathlib import Path

# Change to backend directory
os.chdir(Path(__file__).parent)

print("=" * 70)
print("Google OAuth Setup for Gmail Access - MANUAL MODE")
print("=" * 70)

# Check dependencies
try:
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print("\n[ERROR] Missing required packages!")
    print("\nInstall them with:")
    print("  pip install google-auth-oauthlib google-auth google-api-python-client")
    sys.exit(1)

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

print("\n" + "=" * 70)
print("STEP 1: Enter Your Credentials")
print("=" * 70)

# Get client credentials
client_id = input("\nEnter your Google Client ID: ").strip()
if not client_id:
    print("[ERROR] Client ID is required!")
    sys.exit(1)

client_secret = input("Enter your Google Client Secret: ").strip()
if not client_secret:
    print("[ERROR] Client Secret is required!")
    sys.exit(1)

user_email = input("Enter your Gmail address (optional, press Enter to skip): ").strip()

# Create client config for OOB (out-of-band) flow
client_config = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

print("\n" + "=" * 70)
print("STEP 2: Authorize Access (Manual)")
print("=" * 70)

try:
    # Create flow
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    
    # Generate authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )
    
    print("\n1. Open this URL in your browser:")
    print("=" * 70)
    print(auth_url)
    print("=" * 70)
    print("\n2. Sign in and authorize the app")
    print("3. You'll see a page with an AUTHORIZATION CODE")
    print("4. Copy that code and paste it below")
    
    # Get authorization code from user
    auth_code = input("\nEnter the authorization code: ").strip()
    
    if not auth_code:
        print("[ERROR] Authorization code is required!")
        sys.exit(1)
    
    print("\n[INFO] Exchanging code for tokens...")
    
    # Exchange code for tokens
    flow.fetch_token(code=auth_code)
    creds = flow.credentials
    
    if not creds or not creds.refresh_token:
        print("\n[ERROR] Failed to get refresh token!")
        print("Make sure you completed the authorization.")
        sys.exit(1)
    
    refresh_token = creds.refresh_token
    
    print("\n" + "=" * 70)
    print("SUCCESS! Got Refresh Token")
    print("=" * 70)
    print(f"\nRefresh Token: {refresh_token[:30]}...{refresh_token[-10:]}")
    
except Exception as e:
    print(f"\n[ERROR] OAuth flow failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Update .env file
print("\n" + "=" * 70)
print("STEP 3: Update .env File")
print("=" * 70)

env_file = Path(".env")

if not env_file.exists():
    print("\n[WARNING] .env file not found. Creating new one...")
    env_content = ""
else:
    print(f"\n[INFO] Reading existing .env file...")
    env_content = env_file.read_text()

# Prepare new values
new_values = {
    "GOOGLE_CLIENT_ID": client_id,
    "GOOGLE_CLIENT_SECRET": client_secret,
    "GOOGLE_REFRESH_TOKEN": refresh_token,
}

if user_email:
    new_values["GOOGLE_API_USER_EMAIL"] = user_email

# Update or add each value
lines = env_content.split("\n") if env_content else []
updated_keys = set()

for i, line in enumerate(lines):
    line_stripped = line.strip()
    if not line_stripped or line_stripped.startswith("#"):
        continue
    
    for key, value in new_values.items():
        if line_stripped.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated_keys.add(key)
            print(f"[OK] Updated {key}")
            break

# Add new keys that weren't found
for key, value in new_values.items():
    if key not in updated_keys:
        lines.append(f"{key}={value}")
        print(f"[OK] Added {key}")

# Write back to file
env_file.write_text("\n".join(lines))

print("\n" + "=" * 70)
print("SETUP COMPLETE!")
print("=" * 70)
print("""
Your Google OAuth credentials have been saved to .env file!

Next steps:
1. Restart your backend server:
   cd backend
   python -m uvicorn app.main:app --reload

2. The backend will now fetch real emails from Gmail!

3. Test it by visiting: http://localhost:5173/emails

Note: Your refresh token will be used to automatically get access tokens.
""")

print("=" * 70)

