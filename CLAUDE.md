# CLAUDE.md — Astraeus AI Developer Guide

This document provides essential context for working on Astraeus AI in Claude Code. Read this first.

---

## Project Summary

**Astraeus AI** is an AI-native video editing platform built from first principles. Unlike most editors that bolt AI features onto existing frameworks, Astraeus uses a **proprietary JSON composition format** that serves as the single source of truth shared across the editor UI, FFmpeg renderer, and AI orchestrator.

### Core Philosophy
- **No vendor lock-in** — zero dependency on Remotion or similar frameworks
- **Composition is sacred** — the JSON schema is the product's core IP
- **AI-native by design** — schema built from day one for LLM interaction
- **Clean layer separation** — UI, composition engine, rendering, and AI never bleed into each other
- **Backend-first development** — every feature is built on a fully working backend first

---

## Architecture at a Glance

```
Frontend (Next.js) → API Gateway (FastAPI) → Three Cores:
  1. Composition Engine (JSON schema + validation)
  2. FFmpeg Render Worker (Celery + Redis)
  3. AI Orchestrator (Claude, HyperFrames, Whisper, ElevenLabs)
  
All backed by PostgreSQL, Redis, DigitalOcean Spaces
```

The **composition JSON** is the architectural spine. Every component reads or writes it.

---

## Phase-Based Roadmap

The project is built across **32 phases** in **7 stages**:

| Stage | Phases | Status | Focus |
|-------|--------|--------|-------|
| 1 — Foundation | 1–4 | 🔲 | Repo, FastAPI, database, JWT auth |
| 2 — Composition & Storage | 5–8 | 🔲 | Composition engine, media uploads, project CRUD |
| 3 — Rendering | 9–13 | 🔲 | Redis, Celery, FFmpeg pipeline, render API |
| 4 — Frontend | 14–20 | 🔲 | Next.js editor UI, timeline, preview, export |
| 5 — Editor Polish | 21–24 | 🔲 | Transitions, captions, undo/redo, audio waveforms |
| 6 — AI Layer | 25–29 | 🔲 | Claude + HyperFrames + Whisper + ElevenLabs |
| 7 — Deployment | 30–32 | 🔲 | Docker, DigitalOcean, CI/CD |

**Current Status:** Not yet started. See `docs/PROJECT_PLAN.md` for detailed phase breakdown with acceptance criteria.

### Key Milestones
- ⬜ MVP Editor (end of Stage 4)
- ⬜ Polished Editor (end of Stage 5)
- ⬜ AI-Native Editor (end of Stage 6)
- ⬜ In Production (end of Stage 7)

---

## Directory Layout — Quick Reference

```
astraeus-ai/
├── frontend/              # Next.js 14 + React 18 + Tailwind + Zustand
├── backend/               # FastAPI service + Celery workers
│   ├── app/               # REST API service
│   ├── composition_engine/    # Core IP — composition schema & logic
│   ├── render_worker/     # FFmpeg rendering pipeline
│   ├── ai_orchestrator/   # AI layer (Claude, HyperFrames, etc.)
│   └── migrations/        # Alembic database migrations
├── docs/                  # Architecture, API, schema docs
├── infra/                 # Nginx, systemd, deployment configs
├── scripts/               # Dev and ops scripts
├── .env.example           # Environment template
└── docker-compose.yml     # Local dev stack
```

**Key Documentation Files:**
- `docs/PROJECT_PLAN.md` — 32-phase build plan with acceptance criteria
- `docs/PROJECT_STRUCTURE.md` — Complete file-level directory layout
- `docs/openapi.yaml` — REST API specification
- `docs/architecture.dsl` — C4 architecture model
- `docs/schema.dbml` — Database schema
- `docs/guides/composition-schema.md` — Composition JSON spec
- `docs/guides/ffmpeg-pipeline.md` — FFmpeg rendering internals
- `docs/guides/ai-integration.md` — AI layer architecture

---

## Key Architectural Patterns

### 1. The Composition JSON (Core IP)

Every video project is a **composition** — a JSON structure representing tracks, clips, overlays, and effects. This is the single source of truth.

**Rules:**
- Composition JSON is **immutable at the database level** — each update creates a version record
- Validation happens through `composition_engine` — no bypasses
- The frontend, FFmpeg renderer, and AI orchestrator all consume this same JSON schema
- Composition is serialized as JSONB in PostgreSQL

### 2. Three-Layer Backend Architecture

```
Router (HTTP endpoint) → Service (business logic) → Model (database ORM)
```

**Pattern:**
- `backend/app/routers/<domain>.py` — FastAPI APIRouter with endpoints
- `backend/app/services/<domain>_service.py` — business logic and validation
- `backend/app/models/<domain>.py` — SQLAlchemy ORM models
- `backend/app/schemas/<domain>.py` — Pydantic request/response schemas

### 3. Frontend State Management

State is split into **logical domains** using **Zustand**:

- `authStore.ts` — current user, tokens, auth state
- `compositionStore.ts` — active project composition (the working copy)
- `editorStore.ts` — editor UI state (selection, zoom, playhead)
- `mediaStore.ts` — media library cache
- `historyStore.ts` — undo/redo stack

**Auto-save rule:** Changes to composition auto-save to the backend (debounced 2s).

---

## Development Workflow

### Local Setup

```bash
# Docker Compose (recommended)
cp .env.example .env
docker-compose up --build

# Services available:
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Working on a Phase

1. Read the phase spec in `docs/PROJECT_PLAN.md`
2. Plan the implementation using the checklist as acceptance criteria
3. Work **backend-first** — get the feature working in the API before touching the frontend
4. Test thoroughly — each phase should have working, verifiable behavior
5. Commit and move on — complete and commit before starting the next phase

---

## Tech Stack Reference

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 · React 18 · TypeScript · Tailwind · Zustand |
| Backend API | FastAPI · Pydantic v2 · SQLAlchemy 2 · Alembic |
| Rendering | FFmpeg · Celery · Redis |
| AI | Anthropic Claude · HyperFrames · OpenAI Whisper · ElevenLabs |
| Database | PostgreSQL 16 |
| Storage | DigitalOcean Spaces (S3-compatible) |
| Auth | JWT (python-jose) |

---

## Important Design Decisions

**ADR-001: No Remotion** — Build framework-independent. Avoids vendor lock-in, enables custom FFmpeg pipeline, preserves composition JSON as core IP.

**ADR-002: Composition as JSONB** — Store as single column, not relational tables. Simpler versioning, flexible for AI modifications.

**ADR-003: Celery + Redis** — Use task queue for async rendering. Scales horizontally, simple job tracking.

**ADR-004: Direct-to-Spaces Upload** — Frontend uploads directly via signed URLs. Reduces backend load, supports large files.

---

## Common Tasks & Where to Find Them

| Task | Location |
|------|----------|
| Add API endpoint | `backend/app/routers/` |
| Modify composition validation | `backend/composition_engine/validator.py` |
| Change FFmpeg behavior | `backend/render_worker/filter_graph.py` |
| Add AI provider | `backend/ai_orchestrator/<provider>_client.py` |
| Build UI component | `frontend/components/<feature>/` |
| Update composition state | `frontend/lib/stores/compositionStore.ts` |
| Add database table | `backend/app/models/` + Alembic migration |
| Change API types | `backend/app/schemas/` |

---

## Key Files & Their Roles

**Backend Core:**
- `backend/app/main.py` — FastAPI app factory
- `backend/app/config.py` — environment variables
- `backend/app/database.py` — SQLAlchemy setup
- `backend/app/core/security.py` — JWT, password hashing

**Composition Engine (Core IP):**
- `backend/composition_engine/schema.py` — Pydantic models
- `backend/composition_engine/validator.py` — validation rules
- `backend/composition_engine/normalizer.py` — sort, snap, normalize
- `backend/composition_engine/serializer.py` — JSON encode/decode

**Rendering Pipeline:**
- `backend/render_worker/parser.py` — composition → render plan
- `backend/render_worker/filter_graph.py` — render plan → FFmpeg command
- `backend/render_worker/executor.py` — FFmpeg subprocess wrapper
- `backend/render_worker/tasks.py` — Celery task definitions

**Frontend:**
- `frontend/lib/stores/compositionStore.ts` — composition state
- `frontend/lib/stores/editorStore.ts` — editor UI state
- `frontend/lib/api/client.ts` — Axios + JWT interceptor
- `frontend/components/timeline/Timeline.tsx` — main timeline
- `frontend/components/preview/PreviewPlayer.tsx` — video player

---

## Testing & Verification

```bash
# Backend
cd backend
pytest                          # Run all tests
pytest tests/test_auth.py       # Specific test
pytest --cov=app tests/         # With coverage

# Frontend
cd frontend
npm test                        # Run tests
npm test timeline               # Specific suite
```

Use interactive API docs at `http://localhost:8000/docs` for manual testing.

---

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Python module | snake_case | `auth_service.py` |
| Python class | PascalCase | `class AuthService:` |
| TypeScript component | PascalCase | `Timeline.tsx` |
| TypeScript hook | camelCase + `use` | `useAutoSave.ts` |
| API endpoint | kebab-case | `/v1/render-jobs` |
| Database table | snake_case + plural | `render_jobs` |
| Environment var | UPPER_SNAKE_CASE | `DATABASE_URL` |

---

## Git Workflow

- **Main branch:** `main` (always deployable)
- **Feature branches:** `feature/<phase-number>-<feature>` (e.g., `feature/01-repo-scaffolding`)
- **Commit messages:** Semantic, referencing phase (e.g., `Phase 2: Add FastAPI skeleton`)
- **One phase per commit:** Don't combine multiple phases

---

## Troubleshooting

**Docker Compose won't start:**
1. Ensure ports 3000, 5432, 6379, 8000 are free
2. Run `docker-compose down && docker-compose up --build`
3. Check logs: `docker-compose logs -f <service>`

**FFmpeg failing:**
1. Verify installed: `ffmpeg -version`
2. Test simple command: `ffmpeg -f lavfi -i testsrc=d=1:s=1920x1080:r=30 -f null -`

**Celery not picking up tasks:**
1. Verify Redis: `redis-cli ping`
2. Worker logs: `celery -A render_worker.worker worker --loglevel=debug`
3. Check registered tasks: `celery -A render_worker.worker inspect registered`

**Migrations failing:**
1. Current status: `alembic current`
2. History: `alembic history`
3. Rollback: `alembic downgrade -1`

---

## Environment Variables (Key Ones)

```bash
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
DO_SPACES_KEY=your-key
DO_SPACES_SECRET=your-secret
DO_SPACES_BUCKET=your-bucket
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
ELEVENLABS_API_KEY=your-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

See `.env.example` for the complete list.

---

## Future-Proofing Checklist

When adding new features:
- [ ] Does it preserve composition JSON as the single source of truth?
- [ ] Is it backend-complete before touching frontend?
- [ ] Are there unit tests for business logic?
- [ ] Is the API spec documented in OpenAPI first?
- [ ] Does it follow three-layer architecture (Router → Service → Model)?
- [ ] Are migrations created for database changes?
- [ ] Is error handling consistent with project's exception patterns?

---

## Getting Help

- **Project plan:** `docs/PROJECT_PLAN.md` for complete phase breakdown
- **API docs:** `http://localhost:8000/docs` (interactive Swagger)
- **Architecture:** `docs/` for C4 diagrams, database schema, OpenAPI spec
- **Composition schema:** `docs/guides/composition-schema.md`
- **FFmpeg pipeline:** `docs/guides/ffmpeg-pipeline.md`
- **AI integration:** `docs/guides/ai-integration.md`

---

## Summary

Astraeus AI is a **32-phase project** building a modern, AI-native video editor from scratch. The **composition JSON** is the architectural spine and core IP. Each phase is self-contained with clear acceptance criteria. Work **backend-first**, follow the **three-layer architecture pattern**, and treat the **composition as sacred**. The documentation is comprehensive — use it.

Happy building! 🚀
