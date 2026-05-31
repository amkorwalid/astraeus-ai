<div align="center">

# ✦ Astraeus AI

**An AI-native video editing platform built from first principles.**

*Proprietary composition engine · FFmpeg rendering core · Claude-powered AI layer*

---

[Overview](#overview) · [Architecture](#architecture) · [Tech Stack](#tech-stack) · [Quick Start](#quick-start) · [Documentation](#documentation) · [Roadmap](#roadmap)

</div>

---

## Overview

**Astraeus AI** is a browser-based video editing platform engineered for the AI era. Unlike most editors that bolt AI features onto a pre-existing core, Astraeus AI is built around a **proprietary JSON composition format** that is natively readable and writable by large language models. This is the platform's core IP — a structured representation of a video project that doubles as a programmable surface for AI agents.

The base editor is built entirely from scratch with **zero dependency on third-party video frameworks** like Remotion. Rendering is powered by **FFmpeg** directly. The AI layer — added once the base editor is stable — uses **HyperFrames** exclusively for AI-generated overlays, captions, and motion graphics orchestrated by **Claude**.

### Why this approach?

- **Independence** — no vendor lock-in to any video framework
- **Ownership** — the composition format is the product's competitive moat
- **AI-native** — schema designed from day one for LLM interaction
- **Composable** — each layer (UI, composition, rendering, AI) is fully decoupled

---

## Architecture

Astraeus AI is organized into four cleanly separated layers:

```
┌─────────────────────────────────────────────────────────┐
│                  Web Application                        │
│      Next.js · React · Tailwind · TypeScript            │
│   Timeline · Preview Player · Media Library · AI UI     │
└────────────────────────┬────────────────────────────────┘
                         │ JSON over HTTPS
┌────────────────────────▼────────────────────────────────┐
│                    API Gateway                          │
│              FastAPI · Pydantic v2 · JWT                │
│   Auth · Projects · Media · Renders · AI Endpoints      │
└──────────┬─────────────┬──────────────┬─────────────────┘
           │             │              │
┌──────────▼──────┐ ┌────▼──────┐ ┌────▼─────────────────┐
│  Composition    │ │  FFmpeg   │ │   AI Orchestrator    │
│  Engine (IP)    │ │  Render   │ │                      │
│                 │ │  Worker   │ │  Claude → HyperFrames│
│  JSON Schema    │ │           │ │  Whisper · ElevenLabs│
│  Validation     │ │  Celery   │ │                      │
│  Normalization  │ │  FFmpeg   │ │  Overlay Compositor  │
└──────────┬──────┘ └────┬──────┘ └────┬─────────────────┘
           │             │             │
┌──────────▼─────────────▼─────────────▼──────────────────┐
│            PostgreSQL · Redis · DO Spaces               │
└─────────────────────────────────────────────────────────┘
```

Full C4 model available in [`docs/architecture.dsl`](./docs/architecture.dsl) — render with [Structurizr](https://structurizr.com).

### The Composition JSON — Core IP

Every video project is a composition. The composition is JSON. The JSON is the source of truth shared across the editor UI, the FFmpeg renderer, and the AI orchestrator. AI agents read and write this format natively — no intermediate translation, no framework wrapper.

```json
{
  "id": "project-uuid",
  "resolution": { "width": 1920, "height": 1080 },
  "fps": 30,
  "duration": 60.0,
  "tracks": [
    { "type": "video", "clips": [...] },
    { "type": "audio", "clips": [...] },
    { "type": "text", "overlays": [...] },
    { "type": "ai_overlay", "source": "hyperframes", "clips": [...] }
  ]
}
```

Full schema documentation in [`docs/openapi.yaml`](./docs/openapi.yaml).

---

## Tech Stack

| Layer | Stack |
|---|---|
| **Frontend** | Next.js 14 · React 18 · TypeScript · Tailwind CSS · Zustand |
| **Backend API** | FastAPI · Pydantic v2 · SQLAlchemy 2 · Alembic |
| **Rendering** | FFmpeg · Celery · Redis |
| **AI Layer** | Anthropic Claude · HyperFrames · OpenAI Whisper · ElevenLabs |
| **Database** | PostgreSQL 16 |
| **Storage** | DigitalOcean Spaces (S3-compatible) |
| **Auth** | JWT (python-jose) |
| **Infra** | Docker · Nginx · DigitalOcean Droplet |

---

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- FFmpeg
- PostgreSQL 16
- Redis
- A DigitalOcean Spaces bucket (or any S3-compatible storage)

### Local Development

**Option A — Docker Compose (recommended)**

```bash
git clone https://github.com/amkorwalid/astraeus-ai.git
cd astraeus-ai
cp .env.example .env
# Fill in your secrets in .env
docker-compose up --build
```

The stack will be available at:
- Frontend → `http://localhost:3000`
- API → `http://localhost:8000`
- API docs → `http://localhost:8000/docs`

**Option B — Run services manually**

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload

# Celery worker (separate terminal)
celery -A render_worker.worker worker --loglevel=info

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

---

## Documentation

All architecture and design documentation lives in the [`docs/`](./docs) directory.

| Document | Description |
|---|---|
| [`PROJECT_PLAN.md`](./docs/PROJECT_PLAN.md) | 32-phase step-by-step build plan |
| [`PROJECT_STRUCTURE.md`](./docs/PROJECT_STRUCTURE.md) | Directory layout and naming conventions |
| [`architecture.dsl`](./docs/architecture.dsl) | C4 architecture model (Structurizr DSL) |
| [`schema.dbml`](./docs/schema.dbml) | Database schema (DBML) |
| [`openapi.yaml`](./docs/openapi.yaml) | Complete REST API specification |
| [`guides/composition-schema.md`](./docs/guides/composition-schema.md) | Composition JSON deep dive |
| [`guides/ffmpeg-pipeline.md`](./docs/guides/ffmpeg-pipeline.md) | How rendering works internally |
| [`guides/ai-integration.md`](./docs/guides/ai-integration.md) | AI layer architecture |
| [`decisions/`](./docs/decisions) | Architecture Decision Records (ADRs) |

---

## Roadmap

Built incrementally across **32 phases** in **7 stages**. Track progress in [`PROJECT_PLAN.md`](./docs/PROJECT_PLAN.md).

| Stage | Status | Description |
|---|---|---|
| 1 — Foundation | 🔲 | Repo, FastAPI skeleton, database, JWT auth |
| 2 — Composition & Storage | 🔲 | Composition engine, media uploads, project CRUD |
| 3 — Rendering | 🔲 | Celery, FFmpeg pipeline, render API |
| 4 — Frontend | 🔲 | Editor UI, timeline, preview, export |
| 5 — Editor Polish | 🔲 | Transitions, captions, undo/redo |
| 6 — AI Layer | 🔲 | Claude + HyperFrames + Whisper + ElevenLabs |
| 7 — Deployment | 🔲 | Docker, DigitalOcean, CI/CD |

### Milestones

- ⬜ **MVP Editor** (end of Stage 4) — fully functional base editor
- ⬜ **Polished Editor** (end of Stage 5) — production-ready editing experience
- ⬜ **AI-Native Editor** (end of Stage 6) — feature-complete platform
- ⬜ **In Production** (end of Stage 7) — live and serving users

---

## Design Principles

1. **Framework-independent base** — the editor core has zero dependency on Remotion or HyperFrames.
2. **HyperFrames scoped to AI only** — used exclusively for AI overlays, never for core editing.
3. **JSON as core IP** — the composition format is the moat. Treat it with care.
4. **AI-native by design** — every schema decision considers how an LLM would read or write it.
5. **Clean layer separation** — UI, composition engine, FFmpeg renderer, and AI orchestrator never bleed into each other.
6. **Backend-first development** — every frontend feature is built on top of a fully working backend.
7. **Composition is sacred** — every change passes through the composition engine. No bypasses.

---

## Repository Layout

```
astraeus-ai/
├── frontend/           # Next.js web application
├── backend/            # FastAPI service + Celery workers
│   ├── app/            # API service
│   ├── composition_engine/   # Core IP — composition logic
│   ├── render_worker/        # FFmpeg rendering pipeline
│   └── ai_orchestrator/      # AI layer (Claude, HyperFrames, ...)
├── docs/               # Architecture, API, schema docs
├── infra/              # Nginx, systemd, deployment configs
├── scripts/            # Dev and ops scripts
└── docker-compose.yml
```

See [`PROJECT_STRUCTURE.md`](./docs/PROJECT_STRUCTURE.md) for the complete file-level layout.

---

## API

The complete REST API is specified in [`docs/openapi.yaml`](./docs/openapi.yaml). At a glance:

| Domain | Endpoints |
|---|---|
| **Auth** | register · login · refresh · logout |
| **Users** | profile · quota |
| **Projects** | CRUD · versions · restore |
| **Media** | signed upload URLs · confirm · list · delete |
| **Renders** | submit · status · list · cancel |
| **AI** | overlay · captions · voiceover · task status |

Interactive API docs are available at `/docs` when the backend is running.

---

## Contributing

This project is currently developed solo. External contributions are not accepted at this stage.

For questions, ideas, or feedback, open an issue.

---

## License

Proprietary. All rights reserved.

The Astraeus AI composition schema, rendering engine, and AI orchestration architecture are proprietary intellectual property.

---

<div align="center">

**Astraeus AI** — *building the editor LLMs deserve.*

</div>