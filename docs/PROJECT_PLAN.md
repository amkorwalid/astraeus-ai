# Astraeus AI — Project Plan

Step-by-step build plan broken into small, focused phases. Each phase produces a working, testable deliverable.

---

## Roadmap Overview

| Stage | Phases | Focus |
|---|---|---|
| **Stage 1 — Foundation** | 1–4 | Project setup, backend skeleton, database, auth |
| **Stage 2 — Composition & Storage** | 5–8 | Composition engine, media uploads, project CRUD |
| **Stage 3 — Rendering** | 9–13 | Redis, Celery, FFmpeg pipeline, render API |
| **Stage 4 — Frontend** | 14–20 | Next.js editor UI, timeline, preview, export |
| **Stage 5 — Editor Polish** | 21–24 | Transitions, captions, undo/redo, audio waveform |
| **Stage 6 — AI Layer** | 25–29 | AI Orchestrator, Claude, HyperFrames, Whisper, ElevenLabs |
| **Stage 7 — Deployment** | 30–32 | Docker, DigitalOcean, CI/CD |

---

# Stage 1 — Foundation

## Phase 1 — Repo Scaffolding

**Goal:** Create the monorepo structure and initial tooling.

- [X] Initialize git repository
- [X] Create directory structure (`frontend/`, `backend/`, `docs/`)
- [X] Copy `README.md`, `openapi.yaml`, `architecture.dsl`, `schema.dbml` to `docs/`
- [X] Add `.gitignore` for Python, Node, env files, FFmpeg outputs
- [X] Add `.env.example` at root
- [X] Initialize `docker-compose.yml` with PostgreSQL and Redis services

**Deliverable:** Clean repo skeleton committed to GitHub.

---

## Phase 2 — Backend Skeleton

**Goal:** Stand up the FastAPI application with health endpoint and config.

- [ ] Create Python virtual environment
- [ ] Install FastAPI, uvicorn, pydantic v2, pydantic-settings
- [ ] Create `app/main.py` with FastAPI app and CORS middleware
- [ ] Create `app/config.py` using `pydantic-settings`
- [ ] Create `app/core/exceptions.py` with global exception handler
- [ ] Implement `GET /v1/health` endpoint
- [ ] Add `requirements.txt`
- [ ] Verify `uvicorn app.main:app --reload` starts cleanly

**Deliverable:** FastAPI service responding to `/v1/health`.

---

## Phase 3 — Database Setup

**Goal:** Connect PostgreSQL, set up SQLAlchemy and Alembic, create base tables.

- [ ] Install SQLAlchemy 2, psycopg2-binary, alembic
- [ ] Create `app/database.py` with engine and session factory
- [ ] Initialize Alembic in `migrations/`
- [ ] Create SQLAlchemy models for `users`, `refresh_tokens` (from DBML)
- [ ] Generate and run first migration
- [ ] Verify tables exist in PostgreSQL via `\dt`

**Deliverable:** Database connected, users and refresh_tokens tables created.

---

## Phase 4 — Authentication

**Goal:** Full JWT auth flow: register, login, refresh, logout.

- [ ] Install python-jose, passlib, bcrypt
- [ ] Create `app/core/security.py` with password hashing and JWT helpers
- [ ] Create Pydantic schemas: `RegisterRequest`, `LoginRequest`, `AuthResponse`
- [ ] Create `auth_service.py` with register, login, refresh, logout logic
- [ ] Create `routers/auth.py` with all auth endpoints
- [ ] Create `dependencies.py` with `get_current_user` dependency
- [ ] Test full flow with curl or HTTPie

**Deliverable:** Working auth — can register, login, get token, hit protected endpoint.

---

# Stage 2 — Composition & Storage

## Phase 5 — Composition Engine (Core IP)

**Goal:** Build the proprietary composition JSON schema and validator.

- [ ] Create `composition_engine/` package
- [ ] Define Pydantic v2 models for all composition types (from OpenAPI):
  - [ ] `Resolution`, `Position`, `TextStyle`, `Animation`, `Transition`
  - [ ] `VideoClip`, `AudioClip`, `TextOverlay`, `ImageOverlay`, `AIOverlayClip`
  - [ ] `Track`, `Composition`
- [ ] Implement `validator.py` (overlap detection, duration validation)
- [ ] Implement `normalizer.py` (sort clips, snap timings)
- [ ] Implement `resolver.py` (track layering and z-index)
- [ ] Implement `serializer.py` (to/from JSON)
- [ ] Write unit tests for each module

**Deliverable:** Importable `composition_engine` library with full test coverage.

---

## Phase 6 — Media Upload

**Goal:** Direct-to-Spaces signed URL upload flow.

- [ ] Install boto3
- [ ] Set up DigitalOcean Spaces bucket and API keys
- [ ] Create `media` SQLAlchemy model and migration
- [ ] Create `services/media_service.py` with signed URL generation
- [ ] Implement `POST /v1/media/upload-url` endpoint
- [ ] Implement `POST /v1/media/confirm` endpoint (creates DB record)
- [ ] Implement `GET /v1/media` (list user media)
- [ ] Implement `DELETE /v1/media/{media_id}` (removes from Spaces and DB)
- [ ] Add media metadata extraction (ffprobe for duration, codec, resolution)

**Deliverable:** Can upload a video file end-to-end via signed URLs.

---

## Phase 7 — Project CRUD

**Goal:** Full project lifecycle with composition JSON.

- [ ] Create `projects`, `project_media` SQLAlchemy models and migration
- [ ] Create `services/project_service.py` with composition validation hook
- [ ] Implement `routers/projects.py`:
  - [ ] `GET /v1/projects` (paginated list)
  - [ ] `POST /v1/projects` (create with default empty composition)
  - [ ] `GET /v1/projects/{id}` (full project + composition)
  - [ ] `PUT /v1/projects/{id}` (update with composition validation)
  - [ ] `DELETE /v1/projects/{id}`
- [ ] Ensure composition is validated through `composition_engine` on every update

**Deliverable:** Can create a project, attach media references, save composition JSON.

---

## Phase 8 — Project Version History

**Goal:** Undo/redo backbone — every composition save creates a version.

- [ ] Create `project_versions` SQLAlchemy model and migration
- [ ] Hook into project update to auto-create version snapshot
- [ ] Implement `GET /v1/projects/{id}/versions` (paginated)
- [ ] Implement `POST /v1/projects/{id}/versions/{version_id}/restore`
- [ ] Cap version history at N versions per project (configurable)

**Deliverable:** Project saves are versioned, restorable.

---

# Stage 3 — Rendering

## Phase 9 — Redis & Celery Setup

**Goal:** Async job infrastructure ready.

- [ ] Install redis, celery
- [ ] Configure Redis connection in `app/config.py`
- [ ] Create `render_worker/worker.py` with Celery app config
- [ ] Create a stub task `ping_task` that returns "pong"
- [ ] Verify worker picks up tasks via `celery -A render_worker.worker worker`

**Deliverable:** Celery worker connected to Redis, can run trivial tasks.

---

## Phase 10 — FFmpeg Foundations

**Goal:** Get FFmpeg working in isolation before wiring to compositions.

- [ ] Verify FFmpeg installed (`ffmpeg -version`)
- [ ] Create `render_worker/executor.py` with FFmpeg subprocess wrapper
- [ ] Create `render_worker/progress.py` parsing FFmpeg stderr for progress
- [ ] Write standalone test: concat 2 video clips → output MP4
- [ ] Write standalone test: mix audio over video
- [ ] Write standalone test: burn text overlay with drawtext filter

**Deliverable:** FFmpeg utilities producing test MP4s manually.

---

## Phase 11 — Composition → Render Plan

**Goal:** Translate composition JSON into an internal render plan.

- [ ] Create `render_worker/parser.py`
- [ ] Parse composition into ordered render stages (video, audio, overlays)
- [ ] Download required media files from DO Spaces to local cache
- [ ] Generate temp file paths for intermediate outputs
- [ ] Write unit tests with sample composition fixtures

**Deliverable:** Composition JSON converts into a structured render plan object.

---

## Phase 12 — FFmpeg Filter Graph Builder

**Goal:** Programmatically build FFmpeg `filter_complex` from render plan.

- [ ] Create `render_worker/filter_graph.py`
- [ ] Support video clip concat with transitions (xfade, fade)
- [ ] Support audio mixing with volume and fade in/out
- [ ] Support text overlay (drawtext)
- [ ] Support image overlay (overlay filter)
- [ ] Generate final FFmpeg command string
- [ ] Write tests with snapshot comparisons of generated commands

**Deliverable:** Filter graph builder producing correct FFmpeg commands for compositions.

---

## Phase 13 — Render Worker & Render API

**Goal:** End-to-end render: API submits job → Celery renders → MP4 in Spaces.

- [ ] Create `render_jobs` SQLAlchemy model and migration
- [ ] Create `services/render_service.py` (enqueue job with composition snapshot)
- [ ] Create `render_worker/tasks.py` with full render task:
  - [ ] Pull job from queue
  - [ ] Parse composition → render plan
  - [ ] Build FFmpeg command
  - [ ] Execute and stream progress to DB
  - [ ] Upload output to Spaces
  - [ ] Mark job completed
- [ ] Implement `routers/renders.py`:
  - [ ] `POST /v1/renders` (submit)
  - [ ] `GET /v1/renders/{job_id}` (status)
  - [ ] `GET /v1/renders` (list)
  - [ ] `DELETE /v1/renders/{job_id}` (cancel)
- [ ] Test full flow: create project → save composition → submit render → download MP4

**Deliverable:** Working backend that renders compositions to MP4 files end-to-end.

---

# Stage 4 — Frontend

## Phase 14 — Next.js Scaffolding

**Goal:** Next.js app with auth pages and layout.

- [ ] `npx create-next-app@latest frontend` with TypeScript, Tailwind, App Router
- [ ] Install dependencies: zustand (state), axios (API), react-hook-form, zod
- [ ] Create `lib/api.ts` axios client with JWT interceptor
- [ ] Create `lib/types.ts` from OpenAPI spec (or use openapi-typescript)
- [ ] Create app layout with dark theme
- [ ] Create `/auth/login` and `/auth/register` pages
- [ ] Implement auth store (zustand) with token persistence

**Deliverable:** Can register, log in, hit protected route from the browser.

---

## Phase 15 — Project Dashboard

**Goal:** List, create, and open projects.

- [ ] Create `/projects` dashboard page
- [ ] Fetch and display project list
- [ ] Create new project modal
- [ ] Project card with thumbnail, name, last modified
- [ ] Delete and archive project actions
- [ ] Navigate to `/editor/[project_id]` on click

**Deliverable:** Full project management UI working against the backend.

---

## Phase 16 — Media Library UI

**Goal:** Upload and manage media files from the browser.

- [ ] Create `components/media/MediaLibrary.tsx`
- [ ] Drag-and-drop upload zone
- [ ] Two-step upload: get signed URL → PUT to Spaces → confirm
- [ ] Upload progress indicator
- [ ] Media grid with thumbnails
- [ ] Filter by type (video, audio, image)
- [ ] Delete media action

**Deliverable:** Users can upload and manage media in their library.

---

## Phase 17 — Editor Shell + Composition State

**Goal:** Editor page layout with composition state management.

- [ ] Create `/editor/[project_id]` page
- [ ] Three-panel layout: media library (left), preview (top right), timeline (bottom)
- [ ] Create composition store (zustand) — single source of truth for editor state
- [ ] Load project composition on mount
- [ ] Auto-save composition on changes (debounced, 2s)
- [ ] Save status indicator

**Deliverable:** Editor shell loads a project, displays its composition state, auto-saves changes.

---

## Phase 18 — Timeline UI — Tracks & Clips

**Goal:** Multi-track timeline with visual clips.

- [ ] Create `components/timeline/Timeline.tsx` with horizontal time ruler
- [ ] Create `components/timeline/Track.tsx` for each track type
- [ ] Render video and audio tracks with clip blocks positioned by time
- [ ] Pixel-per-second zoom control
- [ ] Add clip from media library (drag from library to track)
- [ ] Click clip to select; show clip properties panel

**Deliverable:** Visual timeline showing the composition's tracks and clips.

---

## Phase 19 — Timeline Interactions — Drag, Trim, Delete

**Goal:** Make clips on the timeline actually editable.

- [ ] Drag clip horizontally to change `startOnTimeline`
- [ ] Drag clip edges to adjust `trimIn` / `trimOut`
- [ ] Right-click context menu (delete, split, properties)
- [ ] Snap to other clips and to playhead
- [ ] Multi-select with shift-click
- [ ] Keyboard shortcuts (Delete, Cmd+Z, Space)

**Deliverable:** Fully interactive timeline editing.

---

## Phase 20 — Preview Player + Text Overlays + Export

**Goal:** Real-time preview of the composition and final export.

- [ ] Create `components/preview/PreviewPlayer.tsx`
- [ ] HTML5 video player synced to playhead
- [ ] Play, pause, seek controls
- [ ] Text overlay editor panel (font, size, color, position)
- [ ] Add text overlay to track via UI
- [ ] Export button → submits render job
- [ ] Render progress modal with polling
- [ ] Download MP4 when complete

**Deliverable:** Complete editor — users can upload, edit, preview, and export videos.

🎉 **Milestone: Base editor MVP complete.**

---

# Stage 5 — Editor Polish

## Phase 21 — Transitions Between Clips

**Goal:** Visual transitions (fade, crossfade, slide).

- [ ] Backend: extend filter graph builder with `xfade` filter logic
- [ ] Frontend: transition picker UI between adjacent clips
- [ ] Preview transitions in player (approximation; real result on export)
- [ ] Transition duration slider

**Deliverable:** Transitions work end-to-end.

---

## Phase 22 — Captions & SRT

**Goal:** Manual caption editor with SRT import/export.

- [ ] Backend: caption track support in composition schema
- [ ] Backend: SRT parser (import) and serializer (export)
- [ ] Frontend: caption editor panel (timed segments)
- [ ] SRT upload button
- [ ] Caption styling controls (font, color, position, background)

**Deliverable:** Captions can be authored, imported, and rendered.

---

## Phase 23 — Image Overlay Track & Audio Waveforms

**Goal:** Image overlays and visual feedback on audio tracks.

- [ ] Frontend: image overlay editor (position, opacity, size)
- [ ] Backend: image overlay filter in filter graph
- [ ] Generate audio waveform data on upload (via FFmpeg)
- [ ] Store waveform JSON in media table
- [ ] Render waveform on audio tracks in timeline

**Deliverable:** Image overlays work; audio tracks show waveforms.

---

## Phase 24 — Undo/Redo

**Goal:** Full undo/redo history in the editor.

- [ ] Frontend: composition history stack in zustand
- [ ] Track every composition mutation
- [ ] Cmd+Z / Cmd+Shift+Z keyboard shortcuts
- [ ] Undo/redo buttons in UI
- [ ] Project version restore from history panel

**Deliverable:** Robust undo/redo across all editor operations.

🎉 **Milestone: Polished editor complete. Ready for AI layer.**

---

# Stage 6 — AI Layer

## Phase 25 — AI Orchestrator Service Setup

**Goal:** Create the AI Orchestrator as a separate service.

- [ ] Create `ai_orchestrator/` package
- [ ] Add `ai_tasks` SQLAlchemy model and migration
- [ ] Create `services/ai_service.py` to dispatch tasks
- [ ] Implement `routers/ai.py`:
  - [ ] `GET /v1/ai/tasks`
  - [ ] `GET /v1/ai/tasks/{task_id}`
- [ ] Task status polling pattern (same as renders)

**Deliverable:** AI task infrastructure in place, ready to plug in providers.

---

## Phase 26 — Claude + HyperFrames Overlay Generation

**Goal:** Prompt → AI overlay clip merged into composition.

- [ ] Install `anthropic` SDK and HyperFrames CLI/SDK
- [ ] Create `ai_orchestrator/claude_client.py`
- [ ] Create `ai_orchestrator/hyperframes_client.py`
- [ ] Build prompt template for HyperFrames HTML generation
- [ ] Create `ai_overlays` SQLAlchemy model and migration
- [ ] Implement `POST /v1/ai/overlay` endpoint
- [ ] Celery task: prompt → Claude → HTML → HyperFrames → MP4 → composition merge
- [ ] Frontend: AI prompt panel in editor with overlay generation button

**Deliverable:** User types a prompt, AI-generated overlay appears on the timeline.

---

## Phase 27 — Auto-Captioning via Whisper

**Goal:** Auto-generate captions from a video's audio.

- [ ] Install `openai` SDK
- [ ] Create `ai_orchestrator/whisper_client.py`
- [ ] Create `captions` SQLAlchemy model and migration
- [ ] Implement `POST /v1/ai/captions` endpoint
- [ ] Celery task: extract audio → Whisper → timed segments → insert as caption track
- [ ] Frontend: "Auto-Caption" button on video clips
- [ ] Caption review panel before applying

**Deliverable:** Whisper-generated captions appear automatically.

---

## Phase 28 — ElevenLabs Voiceover

**Goal:** Script-to-voice generation.

- [ ] Create `ai_orchestrator/elevenlabs_client.py`
- [ ] Create `voiceovers` SQLAlchemy model and migration
- [ ] Implement `POST /v1/ai/voiceover` endpoint
- [ ] Voice selection (fetch available voices from ElevenLabs)
- [ ] Celery task: script → ElevenLabs → audio file → add as audio track
- [ ] Frontend: voiceover panel with voice picker and script input

**Deliverable:** AI voiceover generated and added to the timeline.

---

## Phase 29 — Script-to-Video Pipeline

**Goal:** Generate full video compositions from a text script.

- [ ] Build prompt template for Claude to generate full composition JSON from script
- [ ] Implement task: script → Claude → composition JSON → save as new project
- [ ] Auto-trigger voiceover generation for narration tracks
- [ ] Auto-trigger HyperFrames for visuals
- [ ] Frontend: "Generate video from script" modal

**Deliverable:** End-to-end AI: text script in, full video composition out.

🎉 **Milestone: Astraeus AI feature-complete.**

---

# Stage 7 — Deployment

## Phase 30 — Dockerization

**Goal:** Fully containerized stack.

- [ ] Write `Dockerfile` for backend (Python + FFmpeg)
- [ ] Write `Dockerfile` for frontend (Next.js)
- [ ] Write `Dockerfile` for render worker (same base + FFmpeg)
- [ ] Update `docker-compose.yml` with all services: postgres, redis, backend, worker, frontend
- [ ] Test full stack starts with `docker-compose up`

**Deliverable:** Whole platform runs locally via Docker Compose.

---

## Phase 31 — DigitalOcean Deployment

**Goal:** Deploy to production on DigitalOcean.

- [ ] Provision DigitalOcean droplet (Ubuntu 22.04) for backend + worker
- [ ] Set up Nginx as reverse proxy with HTTPS (Let's Encrypt)
- [ ] Configure systemd services for uvicorn and Celery worker
- [ ] Deploy frontend to Vercel or DigitalOcean App Platform
- [ ] Point production DNS
- [ ] Configure DigitalOcean Spaces bucket
- [ ] Set production environment variables

**Deliverable:** Astraeus AI live at production URL.

---

## Phase 32 — CI/CD & Monitoring

**Goal:** Automated deploys and observability.

- [ ] Set up GitHub Actions for backend tests on PR
- [ ] Set up GitHub Actions for frontend builds on PR
- [ ] Automated deployment on merge to `main`
- [ ] Set up structured logging (JSON logs to stdout)
- [ ] Configure log aggregation (Logtail, Papertrail, or self-hosted)
- [ ] Set up basic uptime monitoring (UptimeRobot or similar)
- [ ] Set up Sentry for error tracking

**Deliverable:** Production-grade ops with automated deploys and monitoring.

🎉 **Milestone: Astraeus AI in production.**

---

# Progress Tracking

| Stage | Phases Complete | Notes |
|---|---|---|
| 1 — Foundation | 0 / 4 | |
| 2 — Composition & Storage | 0 / 4 | |
| 3 — Rendering | 0 / 5 | |
| 4 — Frontend | 0 / 7 | |
| 5 — Editor Polish | 0 / 4 | |
| 6 — AI Layer | 0 / 5 | |
| 7 — Deployment | 0 / 3 | |
| **Total** | **0 / 32** | |

---

# Working Principles

- **One phase at a time.** Complete and commit before moving to the next.
- **Test as you go.** Each phase should have working, verifiable behavior.
- **Defer polish.** Functional first, beautiful second.
- **Backend before frontend.** Frontend phases assume the backend already works.
- **Composition is sacred.** Every change touches the JSON schema — keep it clean.
- **AI is layered on top.** Never make the base editor depend on AI services.