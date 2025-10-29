# AI Features Setup Guide

## 🚨 IMPORTANT: Enable AI Features

Your backend is currently using **fallback responses** (templates) instead of real AI because the OpenAI API key is not configured.

## Current Status

### ✅ What's Working:
- Backend API is running correctly
- All endpoints are accessible
- OpenAPI integration is enabled
- Frontend calls the backend API properly

### ❌ What's NOT Working:
- **AI features are using template fallbacks**
- No actual LLM (Language Model) calls
- Limited functionality for:
  - Summarization
  - Quiz generation
  - Todo extraction
  - Email summaries

## How to Enable Real AI

### Step 1: Get an OpenAI API Key

1. Visit https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

**Cost Note:** 
- GPT-4o-mini is very affordable (~$0.15 per 1M tokens)
- For testing/learning, $5 credit should last weeks
- You can set usage limits in OpenAI dashboard

### Step 2: Configure the Backend

1. Open `backend/.env` file (already created for you)
2. Add your API key:
   ```env
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
3. Save the file

### Step 3: Restart the Backend

```bash
cd backend
# Stop the current backend (Ctrl+C)
poetry run uvicorn app.main:app --reload
```

You should see in the logs:
```
INFO: Application startup complete
```

If the API key is missing, you'll see:
```
WARNING: OPENAI_API_KEY missing or langchain-openai unavailable; using fallbacks
```

### Step 4: Test AI Features

Visit the frontend and try:

1. **Summarize** (`/summarize`):
   - Paste some text
   - Click "Generate summary"
   - You should see: `fallback_used: false` in the response

2. **Quiz** (`/quiz`):
   - Enter study notes
   - Click "Generate quiz"
   - Questions should be contextually relevant (not templates)

3. **Todo Extract** (`/todo`):
   - Paste meeting notes or tasks
   - Click "Extract tasks"
   - Should intelligently extract action items

## How to Verify AI is Working

### Method 1: Check API Response

Open Browser DevTools (F12) → Network tab → Make a request:

**With AI Working:**
```json
{
  "summary": { ... },
  "fallback_used": false,  // ← Should be false!
  "truncated": false
}
```

**Without AI (Fallback):**
```json
{
  "summary": { ... },
  "fallback_used": true,  // ← Currently true!
  "truncated": false
}
```

### Method 2: Check Backend Logs

When AI is working, you'll see:
```
INFO: LLM initialized with model: gpt-4o-mini
```

When using fallbacks:
```
WARNING: OPENAI_API_KEY missing or langchain-openai unavailable; using fallbacks
```

### Method 3: Quality of Responses

**Fallback responses:**
- Generic quiz questions
- Simple bullet-point summaries
- Basic task extraction

**Real AI responses:**
- Contextually relevant questions
- Detailed, nuanced summaries
- Intelligent task parsing with dates

## Configuration Options

### OpenAI Model Selection

In `backend/.env`:

```env
# Fast and cheap (recommended for development)
OPENAI_MODEL=gpt-4o-mini

# More capable but slower/expensive
OPENAI_MODEL=gpt-4o

# Legacy model (not recommended)
OPENAI_MODEL=gpt-3.5-turbo
```

### Optional: Add Weather API

For the travel advice feature:

1. Get free API key: https://openweathermap.org/api
2. Add to `.env`:
   ```env
   OPENWEATHER_API_KEY=your-weather-api-key
   ```

## Architecture Overview

### Current Flow (HOW IT WORKS)

```
┌─────────────┐      HTTP Request      ┌──────────────┐
│   Frontend  │  ─────────────────────> │   Backend    │
│  (React)    │                         │  (FastAPI)   │
└─────────────┘                         └──────────────┘
                                               │
                                               │ Uses
                                               ▼
                                        ┌──────────────┐
                                        │  LLMService  │
                                        │  (llm.py)    │
                                        └──────────────┘
                                               │
                      ┌────────────────────────┴─────────────────────┐
                      │                                              │
                  ✅ Has API Key?                              ❌ No API Key?
                      │                                              │
                      ▼                                              ▼
              ┌───────────────┐                            ┌────────────────┐
              │   OpenAI API  │                            │   Fallback     │
              │   (ChatGPT)   │                            │   Templates    │
              └───────────────┘                            └────────────────┘
```

### Backend Service Files

All AI features use the **same backend API architecture**:

- `backend/app/services/llm.py` - Core LLM wrapper
- `backend/app/services/summary.py` - Summarization logic
- `backend/app/services/quiz.py` - Quiz generation
- `backend/app/services/todo.py` - Task extraction
- `backend/app/services/email_summary.py` - Email summaries

### API Endpoints Using AI

| Feature | Endpoint | Method | Uses AI |
|---------|----------|--------|---------|
| Summarize | `/study/summarize` | POST | ✅ Yes |
| Quiz | `/study/quiz` | POST | ✅ Yes |
| Todo Extract | `/todo/extract` | POST | ✅ Yes |
| Email Summary | `/emails/top` | GET | ✅ Yes |
| Travel Advice | `/travel/advise` | POST | ⚠️ Weather API |
| Places Search | `/places` | GET | ❌ No (fuzzy search) |
| Digest Preview | `/digest/preview` | GET | ✅ Yes (emails) |

## Performance Comparison

### Without OpenAI (Fallback Mode) - Current State

```python
# llm.py line 62-64
if not api_key or ChatOpenAI is None:
    logger.warning("OPENAI_API_KEY missing; using fallbacks")
    return None  # ← No LLM initialized!
```

**Performance:**
- ⚡ Very fast (no API calls)
- 💰 Free
- ❌ Poor quality (templates)
- ❌ No context understanding
- ❌ Generic responses

### With OpenAI (Real AI)

```python
# llm.py line 66-67
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
return ChatOpenAI(model=model, temperature=0.2, timeout=20)
```

**Performance:**
- ⏱️ Slower (0.5-2s per request)
- 💰 Very affordable (~$0.01 per 10 requests)
- ✅ High quality responses
- ✅ Context-aware
- ✅ Intelligent parsing

## Troubleshooting

### Issue: "OPENAI_API_KEY missing" warning

**Solution:**
1. Check `backend/.env` file exists
2. Verify API key is set: `OPENAI_API_KEY=sk-...`
3. Restart backend server

### Issue: "Invalid API key" error

**Solution:**
1. Verify key is correct (no extra spaces)
2. Check key is active at https://platform.openai.com/api-keys
3. Ensure you have credits in your OpenAI account

### Issue: Slow responses

**Solution:**
1. Responses are cached (24hr) for identical requests
2. Use `gpt-4o-mini` (faster than `gpt-4o`)
3. Consider adding Redis for better caching:
   ```env
   REDIS_URL=redis://localhost:6379
   ```

### Issue: High costs

**Solution:**
1. Responses are cached automatically
2. Set usage limits in OpenAI dashboard
3. Use `gpt-4o-mini` (10x cheaper than gpt-4)

## Summary

✅ **Your architecture is CORRECT** - Frontend → Backend API → LLM  
❌ **Missing:** OpenAI API key in `backend/.env`  
🔧 **Fix:** Add API key and restart backend  
✨ **Result:** Real AI responses instead of templates  

The system is designed to use the backend API - you just need to enable the AI by adding your OpenAI API key!

