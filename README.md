# 📚 ELEC5620 Study Companion - Group 78

An AI-powered study companion application featuring intelligent content summarization, quiz generation, code execution sandbox, and productivity tools.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (Anaconda/Miniconda recommended)
- **Node.js 18+** and npm
- **API Keys** (Required):
  - **OpenAI API Key** - For AI features (quiz, summarization, code generation)
  - **OpenWeather API Key** - For weather/travel features
  - **Google Cloud credentials** - For Gmail/Calendar integration (optional)

**📦 Installation Summary:**
```bash
# Backend (from project root)
cd backend && pip install -r requirements.txt

# Frontend (from project root) 
cd frontend && npm install
```
All dependencies are included in their respective `requirements.txt` and `package.json` files!

### 📦 Setup Instructions

#### 1. Backend Setup (Python)

```bash
# Navigate to backend directory
cd backend

# (Optional) Activate your conda/virtual environment
# conda activate elec5620-clean  # if using conda
# source venv/bin/activate        # if using venv on Linux/Mac
# venv\Scripts\activate           # if using venv on Windows

# Install ALL Python dependencies with ONE command
pip install -r requirements.txt

# Create .env file with required environment variables
# Copy .env.example to .env and fill in your API keys
```

**⚠️ Important: If you installed dependencies before, reinstall them:**
```bash
# If you previously installed without email-validator or testing packages
cd backend
pip install -r requirements.txt --upgrade
```

**✅ What's Included in requirements.txt:**
- ✅ FastAPI & Uvicorn (Web framework)
- ✅ SQLAlchemy & Alembic (Database)
- ✅ OpenAI & LangChain (AI features)
- ✅ Google APIs (Gmail/Calendar)
- ✅ Email validator (Email validation)
- ✅ Pytest & Coverage (Testing)
- ✅ All other required dependencies

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

### 🔐 First Time Setup & Login

When you first access the application at http://localhost:5173:

1. You'll be directed to the **Login Page**
2. **Sign Up**: Create an account with any email and password (6+ characters)
3. **Login**: Sign in with your credentials
4. Your session is saved locally - return anytime without re-logging in
5. View your account details in **Settings** and sign out when done

**Note**: This is a demonstration app with simplified authentication for educational purposes.

#### 🔄 Clear Login Session

If you need to start fresh or test the login page:

1. Open browser **Developer Console** (Press **F12** or **Ctrl+Shift+J** / **Cmd+Option+J**)
2. Click the **Console** tab
3. Type: `localStorage.clear()`
4. Press **Enter**
5. Refresh the page (**F5**)

You'll be redirected to the login page with a clean session.

## 🎯 Features

### 📚 Study & Learning
- **📝 Content Summarization** - Summarize text or web pages with AI-generated structured notes and key points
- **🎓 Quiz Generation** - Generate interactive MCQ quizzes from study materials with explanations
- **🗓️ Study Plan Creator** - Generate personalized study schedules with calendar integration (.ics export)
- **📊 Study Progress Tracking** - Track study sessions and monitor learning progress

### 💻 Code Development Tools
- **💻 Code Generator** - Generate code from natural language descriptions in Python, JavaScript, TypeScript
- **🔬 Code Sandbox** - Execute code safely with AI-powered pre-execution safety analysis and post-execution insights
- **🎯 Smart Code Analysis** - LLM-based code review for safety, performance, and best practices

### 📧 Email & Communication
- **📧 Email Summary Dashboard** - View and summarize your top 18 recent emails with AI categorization
- **📬 Daily Digest** - Automated email digest with highlights, action items, and deadlines
- **🔔 Smart Digest Scheduling** - Configure custom delivery times with timezone support
- **✅ Action Item Extraction** - Automatically identify tasks and deadlines from emails

### 🌍 Travel & Location
- **🌤️ Travel Advisor** - Weather-aware travel recommendations with departure time suggestions
- **🎒 Smart Packing Assistant** - Context-aware item recommendations (umbrella, jacket, water bottle)
- **🗺️ Location Search** - Discover study spots, cafes, and campus locations with quick navigation
- **📍 Route Integration** - Direct Google Maps links for easy navigation

### ⚙️ Productivity & Settings
- **🔐 User Authentication** - Secure login and session management
- **⚙️ Preferences Management** - Customize digest settings, timezone, and notification preferences
- **📅 Google Calendar Integration** - Sync study plans with Google Calendar (optional)
- **🔗 Gmail Integration** - Access Gmail for email summaries (optional)
- **🌓 Dark/Light Mode** - Customizable theme support

### 🔧 System Features
- **⚡ Real-time API** - Fast async backend with automatic API documentation
- **💾 Local Database** - SQLite storage for notes, quizzes, and user data
- **🔄 Caching Layer** - Redis-based caching for improved performance
- **📊 Health Monitoring** - Built-in health check endpoint for system status
- **🎨 Modern UI** - Responsive design with smooth animations and accessible components

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

## 🧪 Development & Testing

### Running Backend Tests

The project includes comprehensive backend tests for API endpoints, services, and business logic.

**Install Testing Dependencies:**
```bash
cd backend

# Make sure ALL dependencies are installed (including testing packages)
pip install -r requirements.txt

# This installs:
# - pytest (test runner)
# - pytest-cov (coverage plugin)
# - pytest-asyncio (async test support)
# - email-validator (required by Pydantic)
# - All other project dependencies
```

**Verify Installation:**
```bash
# Check if pytest is installed
pytest --version

# Should show: pytest 8.x.x
```

**Run All Tests:**
```bash
cd backend
pytest
```

**Run Tests with Coverage Report:**
```bash
cd backend

# Terminal coverage report with missing lines
pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report (recommended)
pytest --cov=app --cov-report=html

# Open the HTML report in your browser
# File location: backend/htmlcov/index.html
```

**Run Specific Test File:**
```bash
cd backend
pytest tests/test_study_plan.py -v
```

**Understanding Coverage Output:**
```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
app/services/travel.py                     45      5    89%   23-27
app/services/quiz.py                      120     30    75%   45-52, 89-95
---------------------------------------------------------------------
TOTAL                                    1234    123    90%
```

- **Stmts**: Total lines of code
- **Miss**: Lines not covered by tests
- **Cover**: Percentage covered
- **Missing**: Specific line numbers not tested

### Backend Testing
```bash
cd backend
poetry run pytest
```

### Type Checking & Linting

**Type Checking:**
```bash
cd backend
mypy app tests  # Requires: pip install mypy
```

**Linting:**
```bash
cd backend
ruff check .  # Requires: pip install ruff
```

**Frontend Type Checking:**
```bash
cd frontend
npm run typecheck
```

## 📝 Advanced Features

This project demonstrates the following advanced technologies:

1. **Application Frameworks**: React (TypeScript), FastAPI
2. **Cloud Services**: OpenAI API, Google Cloud (Gmail/Calendar)
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
- **Reinstall all dependencies**: `cd backend && pip install -r requirements.txt`
- Verify dependencies are installed: `pip list`
- If you see import errors, make sure you're in the correct project directory

### Frontend won't start
- Check Node.js version: `node --version` (should be 18+)
- Delete `node_modules` and run `npm install` again
- Clear Vite cache: `rm -rf frontend/.vite`

### Login issues
- **Automatically redirected to dashboard?** You're already logged in from a previous session
  - To logout: Go to **Settings** → Click **Logout**
  - To clear session: Open Console (**F12**) → Type `localStorage.clear()` → Refresh
- **Stuck on login page**: Clear browser localStorage and refresh (see "Clear Login Session" above)
- **Can't access dashboard**: Make sure you've entered a valid email format and password (6+ characters)
- **Forgot your session**: Just sign up again with any credentials - no data is permanently stored

### Testing issues
- **Missing email-validator error**: Run `pip install -r requirements.txt` to install all dependencies
- **"Unknown pytest.mark.asyncio" warning**: This is normal, tests will still run
- **Import errors**: Make sure you're running pytest from the `backend` directory
- **"No module named 'app'" error**: Use `python -m pytest` instead of just `pytest`
- **Old backup conflicts**: Delete any old project folders that might be in your Python path

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