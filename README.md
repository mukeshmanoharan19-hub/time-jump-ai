# TimeJump AI

AI-powered semantic search over **Microsoft Teams meeting recordings**. Paste a recording URL, sign in with Microsoft, ingest temporarily, search in natural language, and jump to the matching timestamp.

**Current status:** Phase 1 — Microsoft OAuth + Graph recording resolve.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, MSAL |
| Backend | FastAPI, Python |
| Jobs | Celery + Redis |
| Vector DB | Qdrant |
| Metadata | PostgreSQL |

## Quick start

1. Copy environment template and fill Azure AD values (see below):

   ```bash
   cp .env.example .env
   ```

2. Start all services:

   ```bash
   make up
   ```

   Or detached: `make up-d`. See `make help` for all targets.

3. Open [http://localhost:3000](http://localhost:3000), sign in with Microsoft, paste a recording URL, click **Resolve**.

### Verify

- Frontend: [http://localhost:3000](http://localhost:3000)
- API health: [http://localhost:8000/health](http://localhost:8000/health)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- URL parser tests: `make backend-test`

### Services (Docker)

| Service | Port | Role |
|---------|------|------|
| web | 3000 | Next.js UI |
| api | 8000 | FastAPI |
| worker | — | Celery worker (stub until Phase 2) |
| beat | — | Celery beat (stub until Phase 4) |
| postgres | 5433 (host) / 5432 (Docker network) | Users + app sessions |
| redis | 6379 | Celery broker |
| qdrant | 6333 | Vector store (Phase 2+) |

## Azure AD app registration (Phase 1)

1. In [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**.
2. Name: `TimeJump AI` (or similar).
3. Supported account types: single tenant (or multitenant if you need it).
4. Redirect URI: platform **Single-page application (SPA)** → `http://localhost:3000`
5. After create, copy **Application (client) ID** and **Directory (tenant) ID** into `.env`:
   - `AZURE_AD_CLIENT_ID` / `NEXT_PUBLIC_AZURE_AD_CLIENT_ID`
   - `AZURE_AD_TENANT_ID` / `NEXT_PUBLIC_AZURE_AD_TENANT_ID`
6. **Certificates & secrets** → new client secret → `AZURE_AD_CLIENT_SECRET` (reserved for future server flows; SPA login uses public client + PKCE).
7. **API permissions** → Microsoft Graph → **Delegated** only (remove any broader defaults):
   - `User.Read` — sign-in / identity
   - `OnlineMeetings.Read` — Teams meetings
   - `Files.Read` — recording files the user can already open (typical Teams → OneDrive/SharePoint link)

   Do **not** add `Files.Read.All`, `Sites.Read.All`, or transcript admin scopes unless a later phase needs them. Transcription falls back to Whisper when no Graph transcript is available.
8. Click **Grant admin consent** only if your tenant requires it for these delegated permissions.
9. Restart `web` / `api` after editing `.env`.

### Auth flow

1. Browser signs in via MSAL (popup + PKCE).
2. Frontend sends the Graph access token to `POST /auth/microsoft`.
3. Backend validates via Graph `/me`, upserts `users`, stores Graph token on `app_sessions`, returns an opaque **session token**.
4. `POST /recordings/resolve` uses that session’s Graph token (backend token broker — downloads will not rely on the browser alone).

## Supported recording URL shapes

| Kind | Example pattern |
|------|-----------------|
| SharePoint Stream | `https://{tenant}.sharepoint.com/.../_layouts/15/stream.aspx?id=/.../file.mp4` |
| Sharing link | `https://{tenant}-my.sharepoint.com/:v:/g/personal/...` |
| Teams | `https://teams.microsoft.com/...` |
| OneDrive short | `https://1drv.ms/v/...` |
| Direct SharePoint media path | `.../Recordings/*.mp4` |

Unsupported hosts/shapes return HTTP 400 with a clear message.

## Phase 1 API

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/auth/microsoft` | — | Exchange Graph access token → app session |
| GET | `/auth/me` | Bearer session | Current user |
| POST | `/auth/logout` | Bearer session | Delete app session |
| POST | `/recordings/resolve` | Bearer session | Normalize URL + Graph driveItem + sibling transcript probe |

## Phased delivery

1. Phase 0 — Foundations (done)
2. **Phase 1 — Auth + Graph access (current)**
3. Phase 2 — Ingest pipeline
4. Phase 3 — Search + jump-to-timestamp
5. Phase 4 — TTL cleanup
6. Phase 5 — Frontend UX
7. Phase 6 — Tests + hardening

## Environment variables

See [`.env.example`](.env.example).

## Privacy

TimeJump is designed for **temporary ingestion only** — transcripts and embeddings expire after the configured TTL (default 24 hours). Graph tokens are stored on server-side app sessions for resolve/download; sign out deletes the session.

## License

TBD
