# Astraeus AI — Project Structure

Complete reference for the project's directory layout, file purposes, and naming conventions.

---

## Top-Level Layout

```
astraeus-ai/
├── frontend/                    # Next.js web application
├── backend/                     # FastAPI service + workers
├── docs/                        # Architecture, API, schema docs
├── scripts/                     # Dev and ops scripts
├── infra/                       # Infrastructure configs (nginx, systemd)
├── .github/                     # GitHub Actions workflows
├── docker-compose.yml           # Local dev stack
├── docker-compose.prod.yml      # Production overrides
├── .env.example                 # Environment template
├── .gitignore
├── README.md
└── PROJECT_PLAN.md
```

---

## Frontend (`frontend/`)

Next.js 14 with App Router, TypeScript, Tailwind CSS.

```
frontend/
│
├── app/                                # Next.js App Router pages
│   ├── (auth)/                         # Auth route group (no layout)
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   │
│   ├── (dashboard)/                    # Authenticated routes group
│   │   ├── layout.tsx                  # Dashboard layout with sidebar
│   │   ├── projects/
│   │   │   ├── page.tsx                # Projects list
│   │   │   └── new/
│   │   │       └── page.tsx            # Create project
│   │   └── editor/
│   │       └── [project_id]/
│   │           └── page.tsx            # Main editor
│   │
│   ├── api/                            # Next.js route handlers (proxies, if any)
│   ├── layout.tsx                      # Root layout
│   ├── globals.css                     # Tailwind imports
│   └── page.tsx                        # Landing / redirect
│
├── components/
│   ├── ui/                             # Generic UI primitives
│   │   ├── Button.tsx
│   │   ├── Modal.tsx
│   │   ├── Input.tsx
│   │   ├── Dropdown.tsx
│   │   ├── Tabs.tsx
│   │   └── Tooltip.tsx
│   │
│   ├── editor/                         # Editor shell components
│   │   ├── EditorShell.tsx             # Three-panel layout
│   │   ├── EditorHeader.tsx
│   │   ├── PropertiesPanel.tsx
│   │   └── SaveIndicator.tsx
│   │
│   ├── timeline/                       # Timeline UI
│   │   ├── Timeline.tsx                # Main timeline container
│   │   ├── TimeRuler.tsx               # Top time axis
│   │   ├── Track.tsx                   # Single track row
│   │   ├── VideoClip.tsx               # Video clip block
│   │   ├── AudioClip.tsx               # Audio clip block
│   │   ├── TextOverlayBlock.tsx        # Text overlay on text track
│   │   ├── ImageOverlayBlock.tsx       # Image overlay block
│   │   ├── AIOverlayBlock.tsx          # AI-generated overlay block
│   │   ├── Playhead.tsx                # Playhead indicator
│   │   ├── TrackControls.tsx           # Mute, solo, lock controls
│   │   └── ZoomControls.tsx
│   │
│   ├── preview/                        # Preview player
│   │   ├── PreviewPlayer.tsx           # HTML5 video player
│   │   ├── PlaybackControls.tsx        # Play, pause, seek
│   │   └── PreviewCanvas.tsx           # Overlay rendering canvas
│   │
│   ├── media/                          # Media library
│   │   ├── MediaLibrary.tsx            # Main panel
│   │   ├── MediaUploader.tsx           # Drag-drop upload zone
│   │   ├── MediaCard.tsx               # Individual media item
│   │   ├── MediaFilters.tsx            # Type/date filters
│   │   └── UploadProgress.tsx
│   │
│   ├── overlays/                       # Overlay editing UI
│   │   ├── TextOverlayEditor.tsx
│   │   ├── ImageOverlayEditor.tsx
│   │   ├── StyleControls.tsx           # Font, color, size
│   │   ├── PositionControls.tsx        # X/Y/anchor
│   │   └── AnimationControls.tsx       # In/out animations
│   │
│   ├── transitions/                    # Transitions UI
│   │   ├── TransitionPicker.tsx
│   │   └── TransitionPreview.tsx
│   │
│   ├── captions/                       # Captions UI
│   │   ├── CaptionEditor.tsx
│   │   ├── CaptionList.tsx
│   │   └── SRTImporter.tsx
│   │
│   ├── ai/                             # AI feature panels
│   │   ├── AIPromptPanel.tsx           # Generic prompt input
│   │   ├── OverlayGenerator.tsx        # Claude + HyperFrames
│   │   ├── AutoCaptionButton.tsx       # Whisper trigger
│   │   ├── VoiceoverPanel.tsx          # ElevenLabs UI
│   │   ├── ScriptToVideoModal.tsx      # Full pipeline
│   │   └── AITaskStatus.tsx            # Polling status display
│   │
│   ├── render/                         # Export / render UI
│   │   ├── ExportButton.tsx
│   │   ├── RenderProgressModal.tsx
│   │   └── DownloadDialog.tsx
│   │
│   ├── projects/                       # Project management
│   │   ├── ProjectCard.tsx
│   │   ├── ProjectGrid.tsx
│   │   ├── CreateProjectModal.tsx
│   │   └── ProjectSettings.tsx
│   │
│   └── auth/
│       ├── LoginForm.tsx
│       ├── RegisterForm.tsx
│       └── AuthGuard.tsx
│
├── lib/
│   ├── api/                            # API client
│   │   ├── client.ts                   # Axios instance + interceptors
│   │   ├── auth.ts                     # Auth endpoints
│   │   ├── projects.ts
│   │   ├── media.ts
│   │   ├── renders.ts
│   │   └── ai.ts
│   │
│   ├── composition/                    # Composition utilities
│   │   ├── builder.ts                  # Composition mutation helpers
│   │   ├── validator.ts                # Client-side composition validation
│   │   ├── defaults.ts                 # Default values for new tracks/clips
│   │   └── time.ts                     # Time/duration math helpers
│   │
│   ├── stores/                         # Zustand state stores
│   │   ├── authStore.ts                # Current user, tokens
│   │   ├── compositionStore.ts         # Active project composition
│   │   ├── editorStore.ts              # Editor UI state (selection, zoom)
│   │   ├── mediaStore.ts               # Media library cache
│   │   └── historyStore.ts             # Undo/redo stack
│   │
│   ├── hooks/                          # React hooks
│   │   ├── useAutoSave.ts
│   │   ├── useKeyboardShortcuts.ts
│   │   ├── useDrag.ts
│   │   ├── useRenderJob.ts             # Poll render job status
│   │   └── useAITask.ts                # Poll AI task status
│   │
│   ├── types/                          # Shared TypeScript types
│   │   ├── api.ts                      # Generated from OpenAPI
│   │   ├── composition.ts              # Composition schema types
│   │   ├── media.ts
│   │   └── render.ts
│   │
│   └── utils/
│       ├── format.ts                   # Time, file size formatters
│       ├── upload.ts                   # Direct-to-Spaces upload
│       └── cn.ts                       # Tailwind class merger
│
├── public/                             # Static assets
│   ├── favicon.ico
│   ├── logo.svg
│   └── fonts/
│
├── styles/                             # Additional global styles (if needed)
│
├── .env.example
├── .env.local                          # gitignored
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── Dockerfile
```

---

## Backend (`backend/`)

FastAPI with three deployable units: **API service**, **Render Worker**, **AI Orchestrator**. They share core libraries.

```
backend/
│
├── app/                                # FastAPI application
│   ├── main.py                         # FastAPI entrypoint, app factory
│   ├── config.py                       # Pydantic Settings (env vars)
│   ├── database.py                     # SQLAlchemy engine, session factory
│   ├── dependencies.py                 # FastAPI dependencies (auth, DB session)
│   │
│   ├── core/                           # Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── security.py                 # JWT, password hashing
│   │   ├── exceptions.py               # Custom exceptions + global handler
│   │   ├── pagination.py               # Pagination helpers
│   │   ├── logging.py                  # Structured logging config
│   │   └── constants.py                # App-wide constants
│   │
│   ├── models/                         # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py                     # Declarative base + mixins
│   │   ├── user.py
│   │   ├── refresh_token.py
│   │   ├── project.py
│   │   ├── project_version.py
│   │   ├── media.py
│   │   ├── project_media.py
│   │   ├── render_job.py
│   │   ├── ai_task.py
│   │   ├── ai_overlay.py
│   │   ├── caption.py
│   │   ├── voiceover.py
│   │   ├── audit_log.py
│   │   └── usage_quota.py
│   │
│   ├── schemas/                        # Pydantic v2 request/response schemas
│   │   ├── __init__.py
│   │   ├── common.py                   # Pagination, error, generic responses
│   │   ├── auth.py                     # Register, login, refresh, auth response
│   │   ├── user.py                     # User profile, quota
│   │   ├── project.py                  # Project CRUD schemas
│   │   ├── project_version.py
│   │   ├── media.py                    # Media + upload URL schemas
│   │   ├── render_job.py
│   │   └── ai_task.py                  # AI overlay, captions, voiceover schemas
│   │
│   ├── routers/                        # FastAPI APIRouter modules
│   │   ├── __init__.py
│   │   ├── health.py                   # GET /health
│   │   ├── auth.py                     # /auth/*
│   │   ├── users.py                    # /users/*
│   │   ├── projects.py                 # /projects/*
│   │   ├── media.py                    # /media/*
│   │   ├── renders.py                  # /renders/*
│   │   └── ai.py                       # /ai/*
│   │
│   ├── services/                       # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── project_service.py
│   │   ├── media_service.py            # Signed URLs, metadata extraction
│   │   ├── render_service.py           # Job enqueueing, status queries
│   │   ├── ai_service.py               # AI task dispatch
│   │   └── quota_service.py
│   │
│   └── middleware/
│       ├── __init__.py
│       ├── cors.py
│       └── request_logger.py
│
├── composition_engine/                 # Core IP — composition schema & logic
│   ├── __init__.py
│   ├── schema.py                       # Pydantic models for composition JSON
│   ├── validator.py                    # Validation rules (overlap, duration)
│   ├── normalizer.py                   # Sort, snap, normalize timings
│   ├── resolver.py                     # Track ordering and z-index
│   ├── serializer.py                   # JSON serialize/deserialize
│   ├── defaults.py                     # Default composition templates
│   └── tests/
│       ├── __init__.py
│       ├── test_schema.py
│       ├── test_validator.py
│       ├── test_normalizer.py
│       └── fixtures/                   # Sample compositions
│
├── render_worker/                      # FFmpeg rendering pipeline
│   ├── __init__.py
│   ├── worker.py                       # Celery app instance
│   ├── tasks.py                        # Celery task definitions
│   ├── parser.py                       # Composition → render plan
│   ├── filter_graph.py                 # FFmpeg filter_complex builder
│   ├── executor.py                     # FFmpeg subprocess wrapper
│   ├── progress.py                     # Progress parsing from stderr
│   ├── output_manager.py               # Upload result to Spaces
│   ├── media_cache.py                  # Local media caching
│   └── tests/
│       ├── __init__.py
│       ├── test_parser.py
│       ├── test_filter_graph.py
│       └── fixtures/
│
├── ai_orchestrator/                    # AI layer — fully decoupled
│   ├── __init__.py
│   ├── prompt_builder.py               # Structured prompts for Claude
│   ├── claude_client.py                # Anthropic SDK wrapper
│   ├── hyperframes_client.py           # HyperFrames API client
│   ├── whisper_client.py               # OpenAI Whisper client
│   ├── elevenlabs_client.py            # ElevenLabs client
│   ├── overlay_compositor.py           # Merge AI clips into composition
│   ├── tasks.py                        # Celery tasks for AI work
│   ├── prompts/                        # Prompt templates
│   │   ├── overlay_generation.md
│   │   ├── script_to_video.md
│   │   └── caption_styling.md
│   └── tests/
│       ├── __init__.py
│       └── test_overlay_compositor.py
│
├── storage/                            # Storage abstractions
│   ├── __init__.py
│   ├── spaces_client.py                # DigitalOcean Spaces (boto3)
│   └── local_storage.py                # Local filesystem (dev)
│
├── migrations/                         # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   ├── alembic.ini
│   └── versions/
│       ├── 001_initial_users.py
│       ├── 002_projects.py
│       └── ...
│
├── tests/                              # Integration tests
│   ├── __init__.py
│   ├── conftest.py                     # Shared pytest fixtures
│   ├── test_auth.py
│   ├── test_projects.py
│   ├── test_media.py
│   ├── test_renders.py
│   └── test_ai.py
│
├── scripts/                            # Backend dev scripts
│   ├── seed_data.py                    # Populate dev DB
│   ├── create_admin.py
│   └── reset_db.py
│
├── .env.example
├── alembic.ini
├── pyproject.toml                      # Or requirements.txt
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile                          # API service
├── Dockerfile.worker                   # Render worker (includes FFmpeg)
└── pytest.ini
```

---

## Docs (`docs/`)

Architecture, API, and database documentation.

```
docs/
├── README.md                           # Main project README
├── PROJECT_PLAN.md                     # Build phase plan
├── PROJECT_STRUCTURE.md                # This file
├── architecture.dsl                    # Structurizr C4 DSL
├── schema.dbml                         # Database design
├── openapi.yaml                        # OpenAPI 3.0 spec
│
├── guides/
│   ├── composition-schema.md           # Composition JSON spec
│   ├── ffmpeg-pipeline.md              # How FFmpeg rendering works
│   ├── ai-integration.md               # AI layer architecture
│   ├── deployment.md                   # Deploy to DigitalOcean
│   └── development.md                  # Local dev setup
│
└── decisions/                          # Architecture Decision Records (ADRs)
    ├── 001-no-remotion.md              # Why no Remotion
    ├── 002-jsonb-composition.md        # Why JSONB over relational
    ├── 003-celery-redis.md             # Why Celery over RQ
    └── 004-direct-spaces-upload.md     # Why signed URLs
```

---

## Infrastructure (`infra/`)

Deployment configs that aren't part of the app code.

```
infra/
├── nginx/
│   ├── astraeus.conf                   # Reverse proxy config
│   └── ssl/                            # gitignored — Let's Encrypt
│
├── systemd/
│   ├── astraeus-api.service            # uvicorn service
│   ├── astraeus-worker.service         # Celery worker service
│   └── astraeus-ai.service             # AI orchestrator service
│
└── digitalocean/
    ├── droplet-setup.sh                # Initial droplet provisioning
    └── deploy.sh                       # Deploy script
```

---

## Scripts (`scripts/`)

Cross-project dev and ops scripts.

```
scripts/
├── dev-up.sh                           # Spin up local dev stack
├── dev-down.sh                         # Tear down
├── db-shell.sh                         # psql into local DB
├── redis-shell.sh                      # redis-cli into local Redis
├── generate-types.sh                   # Generate TS types from OpenAPI
└── lint.sh                             # Lint both frontend and backend
```

---

## GitHub Actions (`.github/workflows/`)

```
.github/
└── workflows/
    ├── backend-tests.yml               # Run pytest on PR
    ├── frontend-tests.yml              # Run lint + build on PR
    ├── deploy-backend.yml              # Deploy on merge to main
    └── deploy-frontend.yml
```

---

## Naming Conventions

### Files

| Type | Convention | Example |
|---|---|---|
| Python module | snake_case | `auth_service.py` |
| Python class | PascalCase | `class AuthService:` |
| Python function/var | snake_case | `def get_user_by_id():` |
| TypeScript component | PascalCase | `Timeline.tsx` |
| TypeScript utility | camelCase | `formatDuration.ts` |
| TypeScript hook | camelCase + `use` | `useAutoSave.ts` |
| API endpoint | kebab-case + plural | `/api/render-jobs` |
| Database table | snake_case + plural | `render_jobs` |
| Database column | snake_case | `created_at` |
| Environment var | UPPER_SNAKE_CASE | `DATABASE_URL` |

### Backend Module Layout

Each FastAPI domain follows the same four-file pattern:

```
models/<domain>.py        # SQLAlchemy ORM model
schemas/<domain>.py       # Pydantic request/response schemas
services/<domain>_service.py  # Business logic
routers/<domain>.py       # FastAPI router with endpoints
```

This is the **three-layer architecture** pattern: Router → Service → Model.

### Frontend Module Layout

Components are grouped by **feature** (`editor/`, `timeline/`, `media/`) rather than by type. Only generic primitives go in `components/ui/`.

---

## Where to Put What — Decision Matrix

| If you're adding... | Put it in... |
|---|---|
| A new database table | `backend/app/models/` + Alembic migration |
| A new Pydantic schema | `backend/app/schemas/` |
| New business logic | `backend/app/services/` |
| A new API endpoint | `backend/app/routers/` |
| Cross-cutting utility (auth, logging) | `backend/app/core/` |
| Composition schema change | `backend/composition_engine/schema.py` |
| New FFmpeg filter | `backend/render_worker/filter_graph.py` |
| New AI provider integration | `backend/ai_orchestrator/<provider>_client.py` |
| New AI workflow | `backend/ai_orchestrator/tasks.py` |
| Generic UI primitive | `frontend/components/ui/` |
| Feature-specific component | `frontend/components/<feature>/` |
| Shared React hook | `frontend/lib/hooks/` |
| Composition mutation logic | `frontend/lib/composition/` |
| API client function | `frontend/lib/api/<domain>.ts` |
| Zustand state slice | `frontend/lib/stores/` |
| Architecture decision | `docs/decisions/` |
| Setup or deploy script | `scripts/` or `infra/` |

---

## Key Architectural Boundaries

1. **`composition_engine` knows nothing about FastAPI, Celery, or HTTP.** It is a pure library importable by any service.

2. **`render_worker` depends on `composition_engine` but not on `app/`.** It is a standalone Celery service.

3. **`ai_orchestrator` depends on `composition_engine` but not on `render_worker`.** It generates composition fragments; rendering happens later.

4. **`app/` (the API) depends on all three** but coordinates rather than implements rendering or AI logic.

5. **Frontend talks only to `app/` via the OpenAPI contract.** It never talks to the worker or AI orchestrator directly.

This separation ensures the composition format remains the only coupling between layers — the platform's core IP.

---

## Quick Navigation Cheatsheet

| Need to... | Go to... |
|---|---|
| Add a new endpoint | `backend/app/routers/` |
| Modify composition rules | `backend/composition_engine/validator.py` |
| Change FFmpeg behavior | `backend/render_worker/filter_graph.py` |
| Add AI feature | `backend/ai_orchestrator/` |
| Edit timeline UI | `frontend/components/timeline/` |
| Update editor state | `frontend/lib/stores/compositionStore.ts` |
| Modify auth flow | `backend/app/routers/auth.py` + `backend/app/services/auth_service.py` |
| Add a DB column | New Alembic migration + update `backend/app/models/` |
| Change API contract | `docs/openapi.yaml` first, then implement |