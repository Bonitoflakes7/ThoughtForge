# ThoughtForge

ThoughtForge is a social thinking platform where people publish ideas, develop them through comments and forks, and discover the perspectives that earn the strongest community signal. It also includes direct and group messaging with real-time delivery.

The product is intentionally designed around evolving ideas rather than a flat social feed:

```text
Original thought
├── comments
├── supportive perspectives
├── challenges
├── refinements
└── extensions
```

## Current status

Phases 1 through 5 are implemented. Phase 6 has search and notifications implemented, with attachments and additional reaction types deferred. Phase 7 has a production-hardening baseline implemented.

See [PROJECT_TRACKER.md](PROJECT_TRACKER.md) for the detailed status, decisions, and change log.

## Technology

- Backend: FastAPI and Python
- Database layer: SQLAlchemy 2.0 async
- Development database: SQLite through `aiosqlite`
- Intended primary database: PostgreSQL through `asyncpg`
- Authentication: JWT access and refresh tokens
- Password hashing: Argon2 through `pwdlib`
- Real-time transport: FastAPI WebSockets
- Frontend: React, TypeScript, and Vite
- Testing: Pytest, HTTPX, backend smoke tests, and frontend production builds

## Project structure

```text
project/
├── backend/
│   ├── app/
│   │   ├── api/                 # Health and system endpoints
│   │   ├── core/                # Config, security, database, dependencies
│   │   └── modules/
│   │       ├── auth/            # Users, JWT, profiles, follows
│   │       ├── thoughts/        # Thoughts, forks, comments, likes, search
│   │       ├── moderation/      # Reports, moderation actions, admin tools
│   │       ├── chat/            # Conversations, messages, WebSockets
│   │       └── notifications/   # In-app notification generation and API
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main application views
│   │   ├── lib/api.ts            # Typed API client
│   │   ├── types.ts              # Shared frontend types
│   │   └── styles.css            # ThoughtForge visual system
│   └── package.json
├── PROJECT_TRACKER.md
└── README.md
```

## Run locally

The current local setup uses SQLite so the application can run without a PostgreSQL service.

### Backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
cd backend
Copy-Item .env.example .env
```

For the current local development setup, set this in `backend/.env`:

```env
DATABASE_URL=sqlite+aiosqlite:///./thoughtforge.db
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

The API is available at:

- Swagger: <http://127.0.0.1:8000/docs>
- Liveness: <http://127.0.0.1:8000/api/v1/health>
- Readiness/database check: <http://127.0.0.1:8000/api/v1/health/ready>

### Frontend

In a second terminal:

```powershell
cd frontend
npm install --cache .npm-cache
npm run dev
```

Open <http://localhost:5173>.

The frontend uses `http://127.0.0.1:8000/api/v1` by default. Set `VITE_API_URL` if the API runs elsewhere.

## Authentication and roles

Authentication uses short-lived JWT access tokens and refresh tokens. Passwords are hashed with Argon2.

- `user` — create thoughts, comment, fork, like, follow, report, and chat
- `moderator` — user permissions plus review reports, hide content, restore content, and inspect moderation history
- `admin` — all permissions plus change roles and activate/deactivate accounts

Moderation is scoped to the thought system. Chat membership and conversation permissions are separate.

## Completed functionality

### Identity and profiles

- Registration and login
- JWT access and refresh tokens
- Current-user endpoint
- Profile updates
- User roles and active/inactive account state
- Follow and unfollow users

### Thought system

- Create, edit, and soft-delete thoughts
- Ranked and recent feeds
- Comments
- Forks with support, challenge, refine, and extend types
- Thought and comment likes
- Engagement counters
- Thought detail view with comments and fork branches
- Search across thought titles and bodies

The top feed ranks original thoughts by likes, then comments, then recency.

### Moderation and administration

- Report thoughts and comments
- Duplicate report prevention
- Moderator report queue
- Dismiss reports
- Hide and restore content
- Moderation audit log
- Admin-only account deactivation
- Admin user list and role management
- Active/Deactivated account indicators in the admin UI

### Chat

- Direct conversations
- Group conversations
- Message history
- WebSocket message delivery
- Presence events
- Typing indicators
- Read receipts
- `Sent` to `Read` state updates in the sender UI
- Group creation with multiple usernames

### Discovery and notifications

- Explore/search view
- In-app notifications for likes, comments, forks, and follows
- Unread notification styling
- Mark-all-as-read action

### Production baseline

- Request IDs through `X-Request-ID`
- Baseline security headers
- Structured request logging
- Database readiness check
- Backend and frontend build verification

## API areas

The complete interactive API is available through Swagger at `/docs`:

```text
/api/v1/auth/*
/api/v1/users/*
/api/v1/thoughts/*
/api/v1/moderation/*
/api/v1/admin/*
/api/v1/chat/*
/api/v1/notifications/*
/api/v1/health
/api/v1/health/ready
```

The chat WebSocket endpoint is:

```text
/ws/chat/{conversation_id}?token=<access_token>
```

WebSocket event types include `message`, `presence`, `typing_start`, `typing_stop`, and `read`.

## Testing guide

### Backend checks

```powershell
cd backend
python -m compileall -q app tests
python -m pytest
```

### Frontend build check

```powershell
cd frontend
npm run build
```

### Authentication smoke test

Through Swagger:

1. Register with `POST /api/v1/auth/register`.
2. Login with `POST /api/v1/auth/login`.
3. Click **Authorize** and enter `Bearer <access_token>`.
4. Call `GET /api/v1/auth/me`.
5. Update the profile with `PATCH /api/v1/auth/me`.
6. Register another user and test follow/unfollow.

### Thought smoke test

1. Create a thought.
2. Add a comment.
3. Create a fork.
4. Like the thought.
5. Open the detail view and confirm comments/forks are returned.
6. Check the ranked feed.

### Moderation smoke test

1. Submit a report through the frontend **Report** action.
2. Promote a test account to moderator or admin in the local SQLite database if needed.
3. Log in again with that account.
4. Open **Moderation desk**.
5. Dismiss or hide the report.
6. For admin testing, change roles and toggle account status in **People & roles**.

### Chat smoke test

1. Log in as User A and open **Messages**.
2. Start a direct message with User B.
3. Send a message.
4. Open the same conversation as User B in another browser/incognito window.
5. Confirm the message arrives live.
6. Type and confirm the typing indicator.
7. Open the conversation as User B and verify User A’s message changes from **Sent** to **Read**.
8. Create and test a group conversation.

### Search and notification smoke test

1. Use **Explore** to search a thought title or body.
2. Have another account like, comment on, fork, or follow the first account’s content.
3. Open **Notifications** as the receiving account.
4. Confirm the new notification is unread.
5. Use **Mark all read** and confirm the unread styling clears.

Notifications are generated for new actions after the notification feature is enabled; older activity is not retroactively converted into notifications.

## Deferred work

- File and image attachments
- Additional reaction types beyond likes
- Rate limiting and abuse throttling
- Redis-backed WebSocket scaling for multiple backend instances
- Database migrations and managed PostgreSQL cutover
- Backups and recovery procedures
- Full security review
- Richer recommendations and reputation scoring
- Mobile-specific navigation polish

## Database note

The application currently runs on SQLite for convenient local testing. The configuration is structured for PostgreSQL through `DATABASE_URL`, but a PostgreSQL connection string and migration workflow should be finalized before production deployment.
