# TimeJump AI

AI-powered semantic search over **Microsoft Teams meeting recordings**. Paste a recording URL, sign in with Microsoft, ingest temporarily, search in natural language, and jump to the matching timestamp.

**Current status:** Phase 0 — foundations (monorepo, Docker, health checks).

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python |
| Jobs | Celery + Redis |
| Vector DB | Qdrant |
| Metadata | PostgreSQL |

## Phase 0 — Run locally

### Prerequisites

- Docker and Docker Compose
- (Optional) Node 22+ and Python 3.12+ for local dev outside Docker

### Quick start

1. Copy environment template:

   ```bash
   cp .env.example .env
   ```

2. Start all services:

   ```bash
   make up
   ```

   Or detached: `make up-d`. See `make help` for all targets.

3. Verify:

   - Frontend: [http://localhost:3000](http://localhost:3000)
   - API health: [http://localhost:8000/health](http://localhost:8000/health)
   - API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

   `/health` should report `healthy` when PostgreSQL, Redis, and Qdrant are up.

### Services (Docker)

| Service | Port | Role |
|---------|------|------|
| web | 3000 | Next.js UI |
| api | 8000 | FastAPI |
| worker | — | Celery worker (stub) |
| beat | — | Celery beat (stub) |
| postgres | 5433 (host) / 5432 (Docker network) | Session metadata (Phase 1+) |
| redis | 6379 | Celery broker |
| qdrant | 6333 | Vector store (Phase 2+) |

## Phased delivery

Work proceeds in gated phases. Phase 0 must be approved before Phase 1 (Microsoft OAuth + Graph) begins.

1. **Phase 0** — Foundations (this phase)
2. Phase 1 — Auth + Graph access
3. Phase 2 — Ingest pipeline
4. Phase 3 — Search + jump-to-timestamp
5. Phase 4 — TTL cleanup
6. Phase 5 — Frontend UX
7. Phase 6 — Tests + hardening

## Environment variables

See [`.env.example`](.env.example). Azure AD and OpenAI keys are required from Phase 1 and Phase 2 onward.

## Privacy

TimeJump is designed for **temporary ingestion only** — transcripts and embeddings expire after the configured TTL (default 24 hours). No permanent knowledge base in the MVP design.

## License

TBD
