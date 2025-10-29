# Google OAuth Setup Guide

Complete guide to set up Gmail integration with OAuth refresh token.

## Quick Start

```bash
cd backend
pip install google-auth-oauthlib google-auth google-api-python-client
python setup_google_oauth.py
```

## Detailed Steps

### 1️⃣ Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "NEW PROJECT"
3. Name: "Study Companion" (or any name)
4. Click "CREATE"

### 2️⃣ Enable Gmail API

1. In the left menu, click "APIs & Services" → "Library"
2. Search for "**Gmail API**"
3. Click on it, then click "**ENABLE**"

### 3️⃣ Create OAuth Credentials

1. Go to "APIs & Services" → "**Credentials**"
2. Click "**+ CREATE CREDENTIALS**" at the top
3. Select "**OAuth client ID**"

#### Configure OAuth Consent Screen (if prompted):

1. Click "CONFIGURE CONSENT SCREEN"
2. Select "**External**" → Click "CREATE"
3. Fill in:
   - App name: `Study Companion`
   - User support email: Your email
   - Developer contact: Your email
4. Click "SAVE AND CONTINUE"
5. Click "ADD OR REMOVE SCOPES"
   - Search for: `gmail.readonly`
   - Check the box for `https://www.googleapis.com/auth/gmail.readonly`
   - Click "UPDATE"
6. Click "SAVE AND CONTINUE"
7. Add Test Users:
   - Click "+ ADD USERS"
   - Enter your Gmail address
   - Click "ADD"
8. Click "SAVE AND CONTINUE"
9. Review and click "BACK TO DASHBOARD"

#### Create OAuth Client ID:

1. Go back to "Credentials"
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Application type: "**Desktop app**"
4. Name: "Study Companion Desktop"
5. Click "**CREATE**"

### 4️⃣ Get Your Credentials

A popup will show your credentials:

```
Client ID: 123456789-abcdefg.apps.googleusercontent.com
Client Secret: GOCSPX-xxxxxxxxxxxxxxxxxxxxx
```

**Either:**
- Copy these values (you'll need them for the script)
- OR click "DOWNLOAD JSON" and use that file

### 5️⃣ Run Setup Script

```bash
cd backend
python setup_google_oauth.py
```

The script will:
1. Ask for your Client ID and Client Secret
2. Open a browser for you to authorize
3. Get the refresh token
4. Automatically save everything to `.env`

### 6️⃣ Complete Authorization

When the browser opens:
1. Sign in with your Google account
2. You'll see "Google hasn't verified this app" - Click "**Continue**" (it's your app!)
3. Check the box "Select all"
4. Click "**Continue**"
5. The page will redirect to `http://localhost:8080/` (this is normal - the script catches it)

### 7️⃣ Verify Setup

Check your `.env` file should now have:

```env
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxx
GOOGLE_REFRESH_TOKEN=1//xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_USER_EMAIL=your.email@gmail.com
```

### 8️⃣ Restart Backend

```bash
cd backend
python -m uvicorn app.main:app --reload
```

You should NO LONGER see warnings about Gmail being unavailable!

### 9️⃣ Test It

Open your frontend:
1. Go to http://localhost:5173/emails
2. You should now see **real emails** from your Gmail inbox!

## Troubleshooting

### "Access blocked: This app's request is invalid"

**Solution:** Make sure you added yourself as a Test User:
1. Go to OAuth consent screen
2. Scroll to "Test users"
3. Add your Gmail address

### "redirect_uri_mismatch"

**Solution:** 
1. Go to Credentials → Your OAuth Client
2. Add `http://localhost:8080/` to "Authorized redirect URIs"
3. Save

### Script says "Failed to get refresh token"

**Solution:** You need to **force consent**:
1. Go to https://myaccount.google.com/permissions
2. Remove "Study Companion" app
3. Run the script again
4. Make sure to click "Continue" through all prompts

### "google_auth_oauthlib module not found"

**Solution:**
```bash
pip install google-auth-oauthlib google-auth google-api-python-client
```

### Backend still uses sample emails

**Solution:**
1. Check `.env` file has all 3 values (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
2. Restart the backend completely (Ctrl+C, then start again)
3. Check backend logs for Gmail-related errors

## What Gets Stored

### `.env` file will contain:

- `GOOGLE_CLIENT_ID` - Your OAuth client ID (public)
- `GOOGLE_CLIENT_SECRET` - Your OAuth client secret (keep private!)
- `GOOGLE_REFRESH_TOKEN` - Long-lived token (keep private!)
- `GOOGLE_API_USER_EMAIL` - Your Gmail address (optional)

### Security Notes:

- ✅ **Refresh token** is stored securely in `.env` (gitignored)
- ✅ Backend automatically gets **access tokens** as needed
- ✅ Access tokens expire after 1 hour (auto-refreshed)
- ❌ **NEVER commit** `.env` to git (it's in `.gitignore`)

## How It Works

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ GET /emails
       ▼
┌─────────────┐
│   Backend   │
└──────┬──────┘
       │ Uses refresh_token
       ▼
┌─────────────┐    1. Get access token
│   Google    │◄───  (using refresh_token)
│   OAuth     │
└──────┬──────┘    2. Returns access token
       │
       ▼
┌─────────────┐    3. Fetch emails
│  Gmail API  │◄───  (using access token)
└──────┬──────┘
       │ 4. Returns emails
       ▼
    Backend
       │ 5. Summarize with AI
       ▼
    Frontend
```

## Revoking Access

To revoke access:
1. Go to https://myaccount.google.com/permissions
2. Find "Study Companion"
3. Click "Remove Access"
4. Delete the tokens from `.env`

## Advanced: Using Downloaded JSON

If you downloaded the OAuth JSON file:

```python
python setup_google_oauth.py --use-json client_secret.json
```

(You'd need to modify the script to accept this parameter)

## Summary

✅ **What you need:**
- Google Cloud project
- Gmail API enabled
- OAuth Client ID + Secret
- Run the setup script

✅ **What you get:**
- Refresh token saved to `.env`
- Real Gmail integration
- AI-powered email summaries

🎉 **Result:** Your app can now read emails from your Gmail! 🎉

