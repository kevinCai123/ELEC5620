# Demo Guide

This guide walks through the ELEC5620 study companion prototype and demonstrates every functional requirement.

## Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) OpenWeather API key for richer travel advice

## Backend

1. Install dependencies and run database migrations:
   `ash
   cd backend
   python -m pip install --upgrade pip
   pip install poetry
   poetry install
   alembic upgrade head
   `
2. Launch the API with UVicorn:
   `ash
   poetry run uvicorn app.main:app --reload
   `
3. API docs are available at http://localhost:8000/docs.
4. Structured JSON logs include equest_id, latency_ms, and fallback flags for observability.

## Frontend

1. Install dependencies and start Vite dev server:
   `ash
   cd frontend
   npm install
   npm run dev
   `
2. Access the UI at http://localhost:5173 (Sentry initialisation is gated behind VITE_SENTRY_DSN).

## Feature Walkthrough

- **Dashboard** – Landing tiles link to every workflow.
- **Top Emails (/emails)** – Lists unread email summaries with fallback indicator. “Open original” deep-links into the sample mailbox.
- **Study Plan (/study/plan)** – Create 3–5 deadlines, persist them, and download duplicate-free ICS exports.
- **Summarize (/summarize)** – Paste text or a URL to generate TL;DR, structured sections, and Q&A seeds. Copy the Markdown output with one click.
- **Quick Quiz (/quiz)** – Build five MCQs from notes, with duplicate detection, template backfill, and rationale hints.
- **Travel Advice (/travel)** – Weather-aware leave-time guidance plus Google Maps walking link; shows fallback message if live data is unavailable.
- **Smart To-Do (/todo)** – Extract editable tasks from pasted text, confirm confidence levels, and store to the metadata-only todo list.
- **Campus Places (/places)** – Fuzzy search curated campus locations, including walking deep-links and no-results guidance.
- **Digest Preview (/digest/preview)** – Inspect the last generated morning digest; sections collapse when no content is available.
- **Settings (/settings)** – Toggle the APScheduler-powered digest, capture preferred time, and update timezone (default Australia/Sydney).

## Background Jobs

- The backend scheduler recomputes the morning digest every minute and only delivers once per user/day. Results are persisted and visible via /digest/preview.

## Code Generation

- After the API is running, generate the typed client consumed by the frontend with:
  `ash
  cd frontend
  npm run api:generate
  `
  Override the schema source by setting SCHEMA_URL.

## Testing & CI

- Backend regression tests:
  `ash
  cd backend
  poetry run pytest
  `
- Frontend quality gates:
  `ash
  cd frontend
  npm run lint
  npm run typecheck
  npm run build
  `
- GitHub Actions workflows (.github/workflows/*.yml) run the same checks on every push/PR.

## Deployment Notes

- Container builds are provided under infra/backend.Dockerfile and infra/frontend.Dockerfile.
- Sample environment variables live in infra/.env.example.
- Refer to infra Dockerfiles for Cloud Run or similar container deployment targets. Configure DATABASE_URL, SENTRY_DSN, and optional providers via secrets.
