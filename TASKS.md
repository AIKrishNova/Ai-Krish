# NEXUS AI — Task Tracker

## Environment findings (Step A)
Ubuntu 24.04, Python 3.12, Node 22, git, make. NOT available: network (PyPI/npm unreachable), Docker, PostgreSQL, Redis.
Not installed: FastAPI, SQLAlchemy, Alembic, httpx, pytest, Next.js. Consequence: framework code cannot be installed, run or tested here.

## Phase 1 — Foundation
- [x] Repo skeleton, .gitignore, .env.example (placeholders only)
- [x] backend/pyproject.toml (dependency floors; unlocked, uninstalled)
- [x] Secret redaction (app/core/redaction.py) — tested
- [x] Password hashing, scrypt (app/core/security.py) — tested
- [ ] Pydantic settings + startup validation (required vs optional)
- [ ] FastAPI app, /health, /api/v1/health/ready, error envelope, CORS
- [ ] SQLAlchemy models + Alembic migration (UUIDs, ownership, audit, usage)
- [ ] Auth: sessions, CSRF, rate limiting, logout
- [ ] Conversation/message routes with ownership checks
- [ ] Next.js shell wired to real endpoints
## Phase 2 — NVIDIA NIM chat
- [x] SSRF URL guard (app/core/urlguard.py) — tested
- [x] Normalized provider errors + bounded backoff (app/providers/errors.py) — tested
- [x] OpenAI-style stream parser + SSE framing (app/providers/parsing.py) — tested
- [ ] AIProvider interface + NVIDIA adapter (httpx) — needs httpx and verification against current NVIDIA docs
- [ ] Streaming chat endpoint, persistence, cancellation, retry/regenerate/edit
- [ ] Live inference: UNVERIFIED (no credentials, no network)
## Phases 3-7: not started
