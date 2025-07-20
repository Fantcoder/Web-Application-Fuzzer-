# Cyber Fuzzer

A full-stack, ML-powered web-application security testing suite.

## Architecture

```
React + Vite + TypeScript (frontend)
        │  Socket.IO (real-time logs & metrics)
        ▼
Python Flask API + ML models (backend)
        │  WebFuzzer (Selenium)  ───▶  Target (e.g. DVWA)
        │  model_training.py     ───▶  *.pkl
        ▼
Supabase Postgres (auth / persistence)
```

## Monorepo layout

```
backend/      Flask + Socket.IO API server
frontend/     Vite/React client app (dark cyberpunk theme)
Webfuzzer.py  Stand-alone fuzzing engine (re-used by backend)
model_training.py  ML pipeline
```

## Quick start (dev)

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py  # runs on http://localhost:5000
```

### 2. Frontend

```bash
cd frontend
npm install # or pnpm install
npm run dev  # opens http://localhost:5173
```

### 3. Environment variables

Create a `.env` file in **frontend/** with:

```
VITE_SUPABASE_URL=your-url
VITE_SUPABASE_ANON_KEY=your-key
VITE_BACKEND_URL=http://localhost:5000
```

Set `SECRET_KEY` env-var for backend if desired.

### 4. Fuzzing

1. Sign-in with Google (handled by Supabase)
2. Navigate to **Fuzzer**
3. Enter the target DVWA URL and click *Start Fuzzing*
4. Real-time logs and dataset metrics stream back to the dashboard.

---

> 🚧  **Work-in-progress** – Several endpoints and payload uploads are stubbed and need completing. See `TODO:` comments throughout the codebase for guidance.