#!/usr/bin/env python3
"""
Google OAuth Setup Script
Guides you through getting a refresh token and saves it to .env file
"""
import os
import sys
from pathlib import Path

# Change to backend directory
os.chdir(Path(__file__).parent)

print("=" * 70)
print("Google OAuth Setup for Gmail Access")
print("=" * 70)

# Check dependencies
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("\n[ERROR] Missing required packages!")
    print("\nInstall them with:")
    print("  pip install google-auth-oauthlib google-auth google-api-python-client")
    sys.exit(1)

# Configuration
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
]
REDIRECT_URI = 'http://localhost:8080/'

print("\n" + "=" * 70)
print("STEP 1: Get Google Cloud OAuth Credentials")
print("=" * 70)
print("""
1. Go to: https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable Gmail API:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Enable Google Calendar API:
   - Still in the Library, search for "Google Calendar API"
   - Click "Enable"
5. Create OAuth credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "CREATE CREDENTIALS" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Study Companion"
   - Click "Create"
6. Configure scopes:
   - Click "Add or remove scopes"
   - Enable:
       • https://www.googleapis.com/auth/gmail.readonly
       • https://www.googleapis.com/auth/gmail.send
       • https://www.googleapis.com/auth/calendar.events
   - Save your changes
7. Download the JSON file or copy the Client ID and Client Secret
""")

print("=" * 70)
print("STEP 2: Enter Your Credentials")
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

# Create client config
client_config = {
    "installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uris": [REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

print("\n" + "=" * 70)
print("STEP 3: Authorize Access")
print("=" * 70)
print("\nA browser window will open. Please:")
print("1. Sign in with your Google account")
print("2. Allow access to Gmail")
print("3. The browser will redirect to localhost (this is normal)")
print("\nPress Enter to continue...")
input()

try:
    # Run OAuth flow
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    print("\n[INFO] Starting OAuth flow...")
    print("[INFO] Opening browser for authorization...")
    
    creds = flow.run_local_server(port=8080, prompt='consent', open_browser=True)
    
    if not creds or not creds.refresh_token:
        print("\n[ERROR] Failed to get refresh token!")
        print("Make sure you completed the authorization in the browser.")
        sys.exit(1)
    
    refresh_token = creds.refresh_token
    
    print("\n" + "=" * 70)
    print("SUCCESS! Got Refresh Token")
    print("=" * 70)
    print(f"\nRefresh Token: {refresh_token[:30]}...{refresh_token[-10:]}")
    
except Exception as e:
    print(f"\n[ERROR] OAuth flow failed: {e}")
    sys.exit(1)

# Update .env file
print("\n" + "=" * 70)
print("STEP 4: Update .env File")
print("=" * 70)

env_file = Path(".env")

if not env_file.exists():
    print("\n[WARNING] .env file not found. Creating new one...")
    env_content = ""
else:
    print("\n[INFO] Reading existing .env file...")
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
lines = env_content.split("\n")
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
   python -m uvicorn app.main:app --reload

2. The backend will now fetch real emails from Gmail!

3. Test it by visiting: http://localhost:5173/emails

Note: Your refresh token will be used to automatically get access tokens.
""")

print("=" * 70)

