# StyleX

Full-stack AI fashion recommendation app: analyse a user's skin tone/undertone and seasonal palette, analyse clothing images, rank items and outfits against that profile, and layer in weather, calendar events and an LLM styling chat.

> **Status: work in progress.** Several features are partial, mocked, or not implemented — see [Known limitations](#known-limitations). No license has been chosen yet, so the code is **not** offered for open-source reuse.

## Architecture

| Layer | Stack |
|---|---|
| Frontend | React 19, Vite, React Router, Zustand, Axios, Framer Motion, CSS Modules |
| Backend | FastAPI, Pydantic, Beanie ODM + Motor (async MongoDB), JWT (python-jose) + bcrypt |
| ML / CV | MediaPipe Face Mesh, OpenCV, PyTorch/torchvision, optional OpenAI CLIP |
| Integrations | Groq (LLaMA 3.3 70B), OpenWeatherMap, Google Calendar OAuth |
| Database | **MongoDB** (required) |

```
styleX/
├── backend/    FastAPI app (app/), scripts/, tests/, Dockerfile
├── frontend/   Vite + React app, Dockerfile
└── docker-compose.yml   MongoDB + backend + frontend
```

## Prerequisites

- Python 3.12, Node.js 20+ (22 recommended)
- MongoDB 6+ — via Docker (recommended) or a local install
- Docker Desktop (optional but easiest)

## Quick start with Docker

```bash
cp backend/.env.example backend/.env      # optional keys can stay as placeholders
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

MongoDB data persists in the `mongo_data` volume. Both backend and frontend hot-reload from your working tree.

## Local development (no Docker for the app)

**1. MongoDB** — must be running before the backend starts:

```bash
docker compose up -d mongo          # or run a local mongod on localhost:27017
```

**2. Backend**

```bash
cd backend
python scripts/setup.py             # creates .venv, installs deps, writes .env with a random SECRET_KEY
# Windows
.venv\Scripts\uvicorn app.main:app --reload
# Linux/macOS
.venv/bin/uvicorn app.main:app --reload
```

**3. Frontend**

```bash
cd frontend
cp .env.example .env                # VITE_API_URL=http://localhost:8000
npm ci
npm run dev
```

## Environment variables

Copy `backend/.env.example` to `backend/.env`. Key variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | `mongodb://localhost:27017` locally, `mongodb://mongo:27017` in Compose |
| `DATABASE_NAME` | default `stylex` |
| `MONGO_MIN_POOL_SIZE`, `MONGO_MAX_POOL_SIZE`, `MONGO_MAX_IDLE_TIME_MS` | connection pool tuning |
| `MONGO_SERVER_SELECTION_TIMEOUT_MS` | how long startup waits for MongoDB (default 5000) |
| `SECRET_KEY` | JWT signing key — **change it** (setup.py generates one) |
| `GROQ_API_KEY` | enables AI chat; without it chat is unavailable |
| `OPENWEATHER_API_KEY` | enables live weather; without it the API returns mock weather |
| `GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI` | Google Calendar OAuth |
| `USE_CLIP`, `USE_GPU`, `USE_FP16` | model options |

Frontend: `VITE_API_URL` (backend base URL).

## If the backend won't start

The API deliberately **does not** fall back to a fake database. If MongoDB is unreachable, startup fails with:

```
RuntimeError: Cannot reach MongoDB at mongodb://localhost:27017. StyleX requires a running MongoDB. ...
```

Start MongoDB (`docker compose up -d mongo`) and re-check `DATABASE_URL`.

## Tests and builds

```bash
cd backend && .venv/Scripts/python -m pytest     # many tests are still placeholders
cd frontend && npm run build && npm run lint     # lint currently reports errors
```

## Known limitations

- **Virtual try-on is not implemented** (stub files only).
- **Fabric detection is placeholder logic**, not a trained model.
- Face/skin analysis is an approximate colour-analysis heuristic, not a medical or clinically validated tool.
- Recommendation scoring is rule-based and has not been validated for quality.
- The frontend auth page currently offers only a simulated demo Google sign-in; email/password UI is planned.
- Google Calendar OAuth needs real credentials and is not production-ready; OAuth state is held in memory.
- Without API keys: weather returns mock data, chat is unavailable.
- Onboarding selfie step is not yet wired to face analysis; several dashboard/recommendation/profile pieces use mock data or placeholder statistics.
- Frontend lint has outstanding errors; most backend tests are placeholders; there is no CI yet.

These are being addressed phase by phase.

## More docs

- [backend/README.md](backend/README.md), [backend/MONGODB_MIGRATION.md](backend/MONGODB_MIGRATION.md), [backend/INTEGRATION.md](backend/INTEGRATION.md)
