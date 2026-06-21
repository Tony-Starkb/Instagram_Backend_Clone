# InstaCore

**A production-style Instagram backend clone built with FastAPI.**

InstaCore replicates the core backend systems behind a social media platform — authentication, posts, social graph (follows), likes, and role-based moderation — built with the same architectural patterns used in real production APIs.

Not a tutorial project. Every design decision — from composite primary keys to token rotation — was made to solve a specific real-world failure mode, not just to make the demo work.

---

## What This Project Demonstrates

- Designing a relational database schema before writing any application code
- Authentication done properly: password hashing, JWT access/refresh tokens, token rotation with breach detection
- Two-layer input validation that blocks privilege escalation at the schema level
- Role-based access control (RBAC) for user / moderator / admin permission tiers
- Middleware for request tracing and structured logging
- Database constraints that make invalid states structurally impossible — not just logically unlikely
- Automated API testing with isolated, disposable test environments

---

## Core Features

### 🔐 Authentication

- Registration with bcrypt password hashing (cost factor 12)
- Login issues a short-lived **access token** (JWT) and a long-lived **refresh token**
- Refresh token stored in an **HttpOnly cookie** — inaccessible to JavaScript, mitigating XSS
- **Token rotation**: every refresh invalidates the previous refresh token and issues a new one
- **Breach detection**: reuse of a revoked refresh token triggers revocation of *all* tokens for that user, forcing full re-authentication

### 👤 Users & Social Graph

- Public user profile lookup by username
- Follow / unfollow system with full edge-case handling:
  - Self-follow attempts blocked (`400`)
  - Duplicate follow blocked (`409`)
  - Unfollowing a user you don't follow blocked (`409`)
- Followers / following list retrieval
- The `follows` table uses a **composite primary key** (`follower_id`, `following_id`) — duplicate follows are impossible at the database level, not just checked in application code

### 📝 Posts

- Full CRUD: create, read, update, delete
- Ownership enforcement — users can only edit or delete their own posts (`403` otherwise)
- Like / unlike system using a composite primary key (`post_id`, `user_id`) on the `post_likes` table — a user cannot like the same post twice, enforced by the schema itself
- Soft-delete pattern via `is_deleted` flag — preserves referential integrity instead of hard-deleting rows

### 🛡️ Role-Based Access Control (RBAC)

Three roles: `user`, `moderator`, `admin` — enforced through a single reusable dependency:

```python
Depends(require_role({"admin", "moderator"}))
```

- **Admin**: change any user's role, ban (delete) any user
- **Moderator + Admin**: delete any post, view any user's full profile (including private accounts)
- Adding a new protected route is one line — no repeated permission-checking logic scattered across files

### 📡 Middleware & Observability

- Every request gets a unique `X-Request-ID` — reused from upstream (CDN/gateway) if present, generated fresh otherwise
- Structured request logging: method, path, status code, duration (using `perf_counter()` for accurate millisecond timing)
- `request_id` included in every error response — enables tracing a specific failed request through logs instantly

### ⚠️ Structured Error Handling

Every error returns the same consistent format — no stack traces, no internal details leaked:

```json
{
  "error": {
    "code": 404,
    "message": "Post with id 3 not found.",
    "request_id": "a373af91-9aa6-46b2-ae64-4b858719294c"
  }
}
```

Custom exception classes (`PostNotFound`, `UserNotFound`, `NotAuthorized`) plus global handlers for validation errors (`422`) and unexpected crashes (`500`, logged internally, never exposed to the client).

### 🧪 Input Validation

Two layers, by design:

**Layer 1 — Pydantic schemas**
- `extra="forbid"` on every schema — a request body containing `role="admin"` during registration is rejected with `422`, not silently ignored
- Response models never include `password_hash` — structurally impossible to leak it
- Field constraints mirror Instagram's real limits (username max 30 chars, bio max 150, caption max 2200)

**Layer 2 — Custom validators**
- Password: minimum 8 characters, requires a letter, number, and special character
- Username: regex-enforced character set, cannot start/end with special characters

### ✅ Automated Tests

Tests spin up a real server on a random port with isolated, temporary data — no shared state between runs. Coverage includes:

- Login success/failure, HttpOnly cookie verification
- Privilege escalation attempts blocked at the schema level
- Full post lifecycle: create → update → delete → confirm `404`
- Like / unlike, including duplicate-action conflict (`409`)
- Validation errors never leak internal stack traces

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Auth | JWT (PyJWT) + bcrypt |
| Validation | Pydantic v2 |
| Testing | Pytest |

---

## Project Structure

```
InstaCore/
│
├── main.py                      # App entry point, middleware & exception handler registration
│
├── routers/
│   ├── auth.py                  # Register, login, refresh, logout
│   ├── users.py                 # Profiles, follow/unfollow, followers/following
│   ├── posts.py                 # Post CRUD, like/unlike
│   ├── admin.py                 # Role management, user banning
│   └── moderate.py              # Post moderation, profile visibility for mods
│
├── database/
│   ├── models.py                # SQLAlchemy models (User, Post, Auth, PostLike, UserFollow)
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── crud.py                   # Database operations
│   └── database.py               # Engine & session setup
│
├── services/
│   ├── dependencies.py          # get_current_user, require_role, token creation/validation
│   └── user_input_validation.py # Password & username validators
│
├── middleware/
│   ├── request_id.py            # X-Request-ID assignment
│   └── logging.py               # Structured request logging
│
├── core/
│   └── exceptions.py            # Custom exception classes
│
├── alembic/                      # Database migrations
├── docs/
│   ├── data-model.md             # Full ER diagram, schema design, indexing rationale
│   ├── erd-diagram.png
│   └── manual-api-testing.md     # Endpoint test cases
├── tests/
│   └── test_api.py               # Automated API test suite
└── docker-compose.yml             # PostgreSQL container
```

---

## Database Schema

| Table | Purpose | Key Design Detail |
|---|---|---|
| `users` | Account data | Role field for RBAC |
| `posts` | User posts | Soft-delete via `is_deleted` |
| `auth_tokens` | Refresh token tracking | Enables revocation & breach detection |
| `post_likes` | Like records | Composite PK `(post_id, user_id)` — duplicate likes impossible |
| `follows` | Social graph | Composite PK `(follower_id, following_id)` — duplicate follows impossible, self-referential FK |

Full entity-relationship diagram and indexing rationale documented in [`docs/data-model.md`](./docs/data-model.md).

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Login — returns access token, sets refresh cookie |
| POST | `/api/v1/auth/refresh` | Rotate refresh token, issue new access token |

### Users
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/users/{username}` | Public profile |
| GET | `/api/v1/users/{username}/posts` | User's posts |
| GET | `/api/v1/users/{username}/followers` | Followers list |
| GET | `/api/v1/users/{username}/following` | Following list |
| POST | `/api/v1/users/{username}/follow` | Follow a user |
| DELETE | `/api/v1/users/{username}/follow` | Unfollow a user |

### Posts
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/posts/{id}` | Get post |
| POST | `/api/v1/posts/` | Create post |
| PATCH | `/api/v1/posts/{id}` | Update own post |
| DELETE | `/api/v1/posts/{id}` | Delete own post |
| POST | `/api/v1/posts/{id}/like` | Like post |
| DELETE | `/api/v1/posts/{id}/like` | Unlike post |

### Admin / Moderation
| Method | Endpoint | Description | Required Role |
|---|---|---|---|
| PUT | `/api/v1/admin/users/{user_id}/role` | Change user role | admin |
| DELETE | `/api/v1/admin/users/{user_id}` | Ban user | admin |
| DELETE | `/api/v1/moderate/posts/{id}` | Delete any post | admin, moderator |
| GET | `/api/v1/moderate/{user_id}` | View any profile | admin, moderator |

### System
| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/v1` | API version info |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start PostgreSQL

```bash
docker-compose up -d
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in:

```
DATABASE_URL=postgresql://user:password@localhost:5432/instacore
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINS=30
REFRESH_TOKEN_EXPIRE_DAYS=7
COOKIE_SECURE=false
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Run the server

```bash
uvicorn main:app --reload
```

API available at `http://127.0.0.1:8000` — interactive docs at `/docs`

### 6. Run tests

```bash
pytest tests/
```

---

## Design Notes

A few decisions worth calling out, since they reflect *why* the project is structured this way:

- **Composite primary keys over application-level checks** — for likes and follows, uniqueness is guaranteed by the database schema itself, not by an `if exists` check that could theoretically race under concurrent requests.
- **`extra="forbid"` on every Pydantic schema** — without this, a request body with an unexpected `role` field could silently succeed and grant elevated permissions. Forbidding extra fields closes that door at the validation layer, before it ever reaches business logic.
- **Refresh token rotation with breach detection** — a stolen refresh token is more dangerous than a stolen access token because it lasts 7 days instead of 30 minutes. Detecting reuse of an already-rotated token and wiping all sessions limits the blast radius of a leaked token.

---

## Status

Actively under development. Auth, posts, social graph, and RBAC are functional and tested. Comments and a feed endpoint are planned next.