# 📚 ELEC5620 Study Companion - Group 78

An AI-powered study companion application featuring intelligent content summarization, quiz generation, code execution sandbox, and productivity tools.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (Anaconda/Miniconda recommended)
- **Node.js 18+** and npm
- **OpenAI API Key** (for AI features)
- **Google Cloud credentials** (for Gmail/Calendar integration)
- **OpenWeather API Key** (for weather features)

### 📦 Setup Instructions

#### 1. Backend Setup (Python with Anaconda)

```bash
# Navigate to backend directory
cd backend

# Activate your conda environment (if using conda)
conda activate elec5620-clean  # or your environment name

# Install Python dependencies
pip install -r requirements.txt

# Install email validator (required for email features)
pip install email-validator

# Create .env file with required environment variables
# Copy .env.example to .env and fill in your API keys
```

**Required Environment Variables (backend/.env):**
```env
DATABASE_URL=sqlite+aiosqlite:///./app.db
OPENAI_API_KEY=your_openai_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
SENTRY_DSN=your_sentry_dsn_here  # Optional
GOOGLE_CLIENT_ID=your_google_client_id  # For Gmail/Calendar
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

**Database Setup:**

The database will be automatically created when you start the backend for the first time.

#### 2. Frontend Setup (Node.js)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### ▶️ Running the Application

#### Terminal 1 - Backend Server:
```bash
cd backend
python -m uvicorn app.main:app --reload
```
Backend will run on: http://localhost:8000

#### Terminal 2 - Frontend Server:
```bash
cd frontend
npm run dev
```
Frontend will run on: http://localhost:5173

### 🌐 Access Points

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **API Redoc**: http://localhost:8000/redoc

### 🔐 First Time Setup

When you first access the application at http://localhost:5173:

1. **Sign Up**: Create an account with any email and password (6+ characters)
2. **Login**: Sign in with your credentials
3. Your session is saved locally - return anytime without re-logging in
4. View your account details in **Settings** and sign out when done

**Note**: This is a demonstration app with simplified authentication for educational purposes.

## 🎯 Features

### AI-Powered Tools
- **📝 Content Summarization** - Summarize text or web pages with structured notes
- **🎓 Quiz Generation** - Generate interactive MCQ quizzes from study materials
- **💻 Code Generator** - Generate code from natural language descriptions
- **🔬 Code Sandbox** - Execute code with AI-powered safety analysis and insights
- **✅ Todo Extraction** - Extract tasks from text using AI
- **📧 Email Summary** - Summarize emails with key action items

### Productivity Tools
- **📅 Calendar Integration** - Sync with Google Calendar
- **📧 Gmail Integration** - Access and manage emails
- **🌤️ Weather Widget** - Current weather information
- **🗓️ Study Schedule** - Plan and track study sessions

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance async web framework
- **SQLAlchemy** - Async ORM with SQLite
- **LangChain** - LLM application framework
- **OpenAI GPT-4o-mini** - AI language model
- **Pydantic** - Data validation
- **Google APIs** - Gmail & Calendar integration

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **TanStack Query** - Data fetching & state management
- **Radix UI** - Accessible component primitives
- **Framer Motion** - Animation library
- **Tailwind CSS** - Utility-first CSS

### DevOps
- **GitHub Actions** - CI/CD pipeline
- **Sentry** - Error tracking and monitoring
- **pytest** - Testing framework
- **mypy** - Static type checking
- **ruff** - Fast Python linter

## 🧪 Development

### Backend Testing
```bash
cd backend
poetry run pytest
```

### Type Checking
```bash
cd backend
poetry run mypy app tests
```

### Linting
```bash
cd backend
poetry run ruff check .
```

### Frontend Type Checking
```bash
cd frontend
npm run typecheck
```

## 📝 Advanced Features

This project demonstrates the following advanced technologies:

1. **Application Frameworks**: React (TypeScript), FastAPI
2. **Cloud Services**: OpenAI API, Google Cloud (Gmail/Calendar), Sentry
3. **Deployment**: GitHub Actions CI/CD
4. **AI Features**:
   - Code generation from natural language
   - AI-powered code execution sandbox with safety analysis
   - Quiz generation with LLM
   - Content summarization
   - Todo extraction
   - Email summarization

## 📄 License

This project is part of ELEC5620 coursework at the University of Sydney.

## 👥 Authors

**Group 78** - ELEC5620 Model Based Software Engineering

---

## 🆘 Troubleshooting

### Backend won't start
- Check that all environment variables are set in `backend/.env`
- Ensure Python 3.11+ is installed: `python --version`
- Verify dependencies are installed: `pip list`
- If you see `ImportError: email-validator is not installed`, run: `pip install email-validator`

### Frontend won't start
- Check Node.js version: `node --version` (should be 18+)
- Delete `node_modules` and run `npm install` again
- Clear Vite cache: `rm -rf frontend/.vite`

### Login issues
- **Stuck on login page**: Clear browser localStorage (F12 → Console → `localStorage.clear()`) and refresh
- **Can't access dashboard**: Make sure you've entered a valid email format and password (6+ characters)
- **Forgot your session**: Just sign up again with any credentials - no data is permanently stored

### Database issues
- Delete `backend/app.db` to reset the database (⚠️ this will delete all stored data)
- The database will be automatically recreated when you restart the backend

### API Key issues
- Verify your OpenAI API key is valid
- Check API key has sufficient credits
- Ensure `.env` file is in the `backend` directory

---

**Happy Studying! 📚✨**

netstat -ano | findstr :8000