# ThoughtForge delivery tracker

This file is the source of truth for the build phases, completed work, decisions, and verification status.

## Status legend

- `[x]` complete and verified
- `[~]` implemented but environment or integration verification is pending
- `[ ]` not started

## Phases

### Phase 1 — Foundation

- [x] FastAPI backend scaffold
- [x] React + TypeScript frontend scaffold
- [x] Environment configuration
- [x] Async SQLAlchemy database wiring
- [x] Docker Compose PostgreSQL and Redis services
- [x] API health endpoint
- [x] Initial ThoughtForge visual direction
- [x] Frontend production build verified
- [~] Backend pytest verification pending Python dependency installation

### Phase 2 — Identity and access

- [x] User model with roles and account status
- [x] Password hashing
- [x] JWT access and refresh tokens
- [x] Registration and login endpoints
- [x] Current-user endpoint
- [x] Profile update endpoint
- [x] Follow/unfollow endpoints
- [x] Role-aware authorization dependencies
- [x] Development database initialization
- [~] Runtime/API tests pending Python dependency installation

### Phase 3 — Thought system

- [x] Thought creation and editing
- [x] Comments
- [x] Forks and thought trees
- [x] Likes and ranking
- [x] Feed and discovery API
- [x] Frontend thought feed UI
- [x] Frontend authentication entry and API client
- [x] Frontend thought composer, detail panel, comments, forks, and likes

### Phase 4 — Moderation

- [x] Reports for thoughts and comments
- [x] Soft deletion and restoration actions
- [x] Moderator dashboard
- [x] Audit log
- [x] Admin-only user deactivation
- [x] Admin user list and role management UI
- [x] Admin account activation/deactivation controls

### Phase 5 — Chat foundation

- [x] Direct conversations
- [x] Group conversations
- [x] WebSocket messaging
- [x] Presence and typing indicators
- [x] Read receipts
- [x] Chat frontend workspace
- [~] Two-browser WebSocket verification pending user testing

### Phase 6 — Product refinement

- [ ] Notifications
- [ ] Search
- [ ] Reactions and attachments
- [ ] Shared thoughts in chat
- [ ] Recommendation and reputation systems

### Phase 7 — Production hardening

- [ ] Rate limiting and abuse controls
- [ ] Redis-backed scaling
- [ ] Observability
- [ ] CI/CD
- [ ] Backups and recovery
- [ ] Security review

## Decisions

- Backend: FastAPI with domain-oriented modules.
- Frontend: React, TypeScript, and Vite.
- Primary database: PostgreSQL; SQLite remains the development fallback until the first managed PostgreSQL connection is supplied.
- Authentication: short-lived JWT access tokens plus rotating refresh tokens.
- Authorization: application roles are `user`, `moderator`, and `admin`.
- Moderation will use soft deletion and auditability rather than irreversible deletion by default.

## Change log

### 2026-09-24

- Added Phase 1 foundation and initial frontend shell.
- Added Phase 2 identity, profiles, follows, roles, and JWT implementation.
- Frontend build passed locally.
- Backend source compilation passed; full backend test execution remains pending dependency installation in the current environment.
- Local PostgreSQL credentials did not match the existing database volume, so development `.env` now uses the supported SQLite fallback; PostgreSQL configuration remains in `.env.example`.
- Added Phase 3 thought, comment, fork, like, ranking, and detail endpoints.
- Added the Phase 3 frontend feed, auth entry, composer, detail panel, comments, forks, and engagement controls.
- Added Phase 4 reports, moderation queue, hide/dismiss/restore actions, audit logs, and admin-only deactivation.
- Added protected admin APIs and the frontend People & roles panel.
- Added explicit Active/Deactivated account badges, row styling, and state-aware Activate/Deactivate labels.
- Added Phase 5 chat models, direct/group conversation APIs, message history, WebSocket events, and chat frontend workspace.
