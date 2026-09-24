# ThoughtForge

ThoughtForge is a social thinking platform where people publish thoughts, develop them through comments and forks, and discover the most constructive perspectives. It also includes direct and group messaging.

## Project layout

- `backend/` — FastAPI API, domain modules, database layer, and tests
- `frontend/` — React + TypeScript client
- `docker-compose.yml` — local PostgreSQL and Redis services

## Phase 1: run locally

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> and check <http://127.0.0.1:8000/health>.

### Tests

```powershell
cd backend
python -m pytest
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://127.0.0.1:8000` for the API.

## Phase 2: identity API smoke test

Start the backend, then use the interactive docs at <http://127.0.0.1:8000/docs>:

1. `POST /api/v1/auth/register` with a username, email, password, and display name.
2. `POST /api/v1/auth/login` with the same email and password.
3. Click **Authorize**, enter `Bearer <access_token>`, and call `GET /api/v1/auth/me`.
4. Call `PATCH /api/v1/auth/me` to update the display name or bio.
5. Register a second user and test `POST /api/v1/users/{username}/follow`.
6. Test `DELETE /api/v1/users/{username}/follow` and confirm it returns `204`.

Expected authorization behavior: missing or invalid tokens return `401`, and a user cannot follow themselves.

## Phase 3: thought system smoke test

After logging in through `/docs`, use the access token with these endpoints:

1. `POST /api/v1/thoughts` to create an original thought.
2. `GET /api/v1/thoughts?sort=top` to see the ranked feed.
3. `POST /api/v1/thoughts/{thought_id}/comments` to add a comment.
4. `POST /api/v1/thoughts/{thought_id}/fork` to create a support, challenge, refine, or extend fork.
5. `POST /api/v1/thoughts/{thought_id}/like` to increase its ranking score.
6. `GET /api/v1/thoughts/{thought_id}` to inspect comments and forks together.

The feed currently ranks original thoughts by likes, then comments, then recency. Forks are ranked inside their parent thought detail response using the same engagement signals.

## Phase 4: moderation smoke test

Reports can be submitted through `POST /api/v1/thoughts/{thought_id}/report` or `POST /api/v1/thoughts/comments/{comment_id}/report`. Moderator/admin accounts can review `GET /api/v1/moderation/reports?status=open` and resolve a report with `PATCH /api/v1/moderation/reports/{report_id}` using one of `dismiss`, `hide`, `restore`, or admin-only `deactivate_user`.

To see the frontend moderation desk, the authenticated user must have the `moderator` or `admin` role. The desk appears in the left navigation and can dismiss reports, hide content, or request author deactivation.

### Local infrastructure

```powershell
docker compose up -d postgres redis
```

PostgreSQL is intentionally configured through `DATABASE_URL`; we will use your connection string when we add the first persistent domain models.
