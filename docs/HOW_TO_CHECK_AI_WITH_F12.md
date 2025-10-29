# How to Check AI is Working Using F12 DevTools

## Step-by-Step Guide

### Step 1: Open the Frontend
1. Make sure frontend is running: `npm run dev` in the `frontend` directory
2. Open browser and go to: **http://localhost:5173**

### Step 2: Open DevTools (F12)
1. Press **F12** on your keyboard (or right-click → "Inspect")
2. Click on the **"Network"** tab at the top
3. Keep DevTools open on the side or bottom

### Step 3: Navigate to Summarize Page
1. In the main browser window, click **"Summarize"** in the sidebar
2. Or go directly to: **http://localhost:5173/summarize**

### Step 4: Enter Text and Generate Summary
1. In the text area, paste some text like:
   ```
   Machine learning is a subset of artificial intelligence that enables 
   computers to learn from data without being explicitly programmed. 
   It uses algorithms to identify patterns and make predictions.
   ```
2. Click **"Generate summary"** button

### Step 5: Find the API Request in Network Tab

In the DevTools Network tab, you'll see new entries appear:

```
Name                    Status    Type        Size    Time
summarize               200       fetch       1.2 KB  850ms
```

**Click on the "summarize" request** (or `/study/summarize`)

### Step 6: Check the Response

After clicking the request, you'll see tabs appear:
- **Headers** (default)
- **Preview**
- **Response** ← Click this one!
- Payload
- Timing

Click the **"Response"** tab to see the JSON data.

## What to Look For

### ✅ AI IS WORKING (Real OpenAI Response)
```json
{
  "summary": {
    "tldr": "Machine learning enables computers to learn from data using algorithms...",
    "sections": [
      {
        "heading": "Core Concepts",
        "bullets": [
          "Subset of artificial intelligence",
          "Learns from data without explicit programming",
          "Uses algorithms for pattern recognition"
        ]
      }
    ],
    "qna_seeds": [...]
  },
  "fallback_used": false,  // ← FALSE = Using real AI!
  "truncated": false
}
```

**Key indicator:** `"fallback_used": false`

### ❌ AI NOT WORKING (Using Templates)
```json
{
  "summary": {
    "tldr": "Machine learning is a subset of artificial intelligence...",
    "sections": [
      {
        "heading": "Key Points",
        "bullets": [
          "Machine learning is a subset of artificial intelligence that enables",
          "computers to learn from data without being explicitly programmed.",
          "It uses algorithms to identify patterns and make predictions."
        ]
      }
    ],
    "qna_seeds": [...]
  },
  "fallback_used": true,  // ← TRUE = Using fallback templates!
  "truncated": false
}
```

**Key indicator:** `"fallback_used": true`

## Visual Guide

### Network Tab Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Elements  Console  Sources  Network ← Click here  ...       │
├─────────────────────────────────────────────────────────────┤
│ 🔍 Filter  📁 All  XHR  Fetch  CSS  JS  ...                 │
├───────┬────────┬──────┬──────┬──────┬──────────────────────┤
│ Name  │ Status │ Type │ Size │ Time │                       │
├───────┼────────┼──────┼──────┼──────┤                       │
│ 📄 summarize  200  fetch  1.2KB  850ms  ← Click this row   │
│ 📄 places     200  fetch  2.4KB  120ms                      │
└───────┴────────┴──────┴──────┴──────┴──────────────────────┘
```

When you click on a request row, the bottom panel shows:

```
┌─────────────────────────────────────────────────────────────┐
│ Headers  Preview  Response ← Click here  Payload  Timing   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ {                                                            │
│   "summary": {                                               │
│     "tldr": "...",                                           │
│     ...                                                      │
│   },                                                         │
│   "fallback_used": false,  ← Look for this!                │
│   "truncated": false                                         │
│ }                                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Tips for Reading Network Tab

### 1. Filter by "Fetch/XHR"
Click the **"Fetch/XHR"** button to hide CSS, JS, images, and only show API calls.

### 2. Use Search
Press **Ctrl+F** in the Network tab and search for:
- `summarize` - for summary requests
- `quiz` - for quiz requests
- `fallback_used` - to find the exact field

### 3. Check Request Payload (What you sent)
Click on a request → **"Payload"** tab to see what data you sent:
```json
{
  "text": "Machine learning is..."
}
```

### 4. Check Response (What you got back)
Click on a request → **"Response"** tab to see what the backend returned.

## Testing Different Features

### Test Quiz Feature
1. Go to **http://localhost:5173/quiz**
2. Enter study notes
3. Click "Generate quiz"
4. Check Network tab for `/study/quiz` request
5. Look for: `"fallback_used": false`

### Test Todo Extraction
1. Go to **http://localhost:5173/todo**
2. Enter meeting notes
3. Click "Extract tasks"
4. Check Network tab for `/todo/extract` request
5. Look for: `"fallback_used": false`

### Test Email Summary
1. Go to **http://localhost:5173/emails**
2. The page loads automatically
3. Check Network tab for `/emails/top` request
4. Look for: `"fallback_used": false`

## Common Issues

### Issue 1: Can't find the request
**Solution:** 
- Make sure Network tab is open BEFORE clicking the button
- Click "Fetch/XHR" filter
- Click the red "Clear" button (🚫) and try again

### Issue 2: Request shows error (red status)
**Solution:**
- Check backend is running
- Look at the "Response" tab for error message
- Common error: `"detail": "OPENAI_API_KEY missing"`

### Issue 3: Response is truncated
**Solution:**
- Right-click on the request
- Select "Copy" → "Copy response"
- Paste into a text editor to see full JSON

## Alternative: Console Method

If you prefer, you can also check in the **Console** tab:

1. Open Console tab (next to Network)
2. Type this and press Enter:
```javascript
fetch('http://localhost:8000/study/summarize', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'Test AI functionality'})
})
.then(r => r.json())
.then(data => {
  console.log('Fallback used:', data.fallback_used);
  console.log('Full response:', data);
});
```

3. Check the output - should say: `Fallback used: false`

## Quick Reference

| Feature | Endpoint | Field to Check |
|---------|----------|----------------|
| Summarize | `/study/summarize` | `fallback_used` |
| Quiz | `/study/quiz` | `fallback_used` |
| Todo Extract | `/todo/extract` | `fallback_used` |
| Email Summary | `/emails/top` | `fallback_used` |
| Travel | `/travel/advise` | `fallback_used` |
| Places | `/places` | N/A (no AI) |

## Summary

✅ **AI Working:** `"fallback_used": false`  
❌ **AI NOT Working:** `"fallback_used": true`  

**Where to check:** F12 → Network tab → Click request → Response tab

That's it! Now you can verify your AI is working properly. 🎉

