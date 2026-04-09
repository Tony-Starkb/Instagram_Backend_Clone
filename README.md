# Instagram Clone — Backend (Month 1)

A backend API built with FastAPI, designed to replicate core Instagram functionality. This project is part of a structured backend learning path, built day by day with real-world patterns in mind.

---

## Day 3 — Status Codes & Structured Error Responses

### What I Learned

One of the most important things a backend API does is return **clear, consistent error responses**. This day was focused on understanding HTTP status codes and making sure every error in the API returns a clean JSON response — no HTML pages, no stack traces, nothing that leaks internal details.

Key status codes covered:
- `200 OK` — successful GET
- `201 Created` — successful POST
- `400 Bad Request` — malformed data
- `401 Unauthorized` — no token or invalid token
- `403 Forbidden` — valid token but not allowed
- `404 Not Found` — post or user doesn't exist
- `409 Conflict` — e.g. liking a post you already liked
- `422 Unprocessable Entity` — valid JSON but fails validation
- `500 Internal Server Error` — something broke on the server side

---

### What I Built

#### 1. Custom Exception Classes (`app/core/exceptions.py`)

Created three custom exception classes that extend FastAPI's `HTTPException`:

- `PostNotFound(post_id)` — raised when a requested post doesn't exist
- `UserNotFound(user_id)` — raised when a requested user doesn't exist
- `NotAuthorized(user_id=None)` — raised when a user tries to do something they're not allowed to. `user_id` is optional because not every 403 is tied to a known user.

Each class passes the correct `status_code` and a human-readable `detail` message directly to `super().__init__()`.

#### 2. Global Exception Handlers (`main.py`)

Registered exception handlers so every error — no matter where it's raised — returns the same structured JSON format:

```json
{
  "error": {
    "code": 404,
    "message": "Post with id 99 not found.",
    "request_id": "a373af91-9aa6-46b2-ae64-4b858719294c"
  }
}
```

Handlers added:
- `PostNotFound` handler
- `UserNotFound` handler
- `NotAuthorized` handler
- `HTTPException` handler — catches all other HTTP errors
- `RequestValidationError` handler — catches 422 validation errors (e.g. passing a string where an integer is expected)
- Generic `Exception` handler — catches unexpected 500 errors, returns a safe generic message with no stack trace

#### 3. `request_id` on Every Error

Every error response includes a unique `request_id` generated with `uuid4()`. This is how real APIs (including Instagram) allow support teams to trace a specific request in logs without exposing internal details to the client.

#### 4. Raising Exceptions in Routes

Updated the posts router to actually raise `PostNotFound` when a post doesn't exist, instead of returning `null`. This was the missing link that connected the exception classes to the handlers.

---

### Error Format

All errors follow this consistent structure:

```json
{
  "error": {
    "code": "<HTTP status code>",
    "message": "<human readable message>",
    "request_id": "<uuid4>"
  }
}
```

No HTML. No stack traces. No internal field names exposed to the client.

---

### How Instagram Does It

Instagram's error responses look like this:
```json
{
  "message": "Sorry, this media has been deleted.",
  "error_type": "APINotFoundError",
  "status": 404
}
```

Clean, structured, no internal details. The global exception handler in this project does the same job — it sits between the application and the client, formatting errors consistently before they go out.

---

### Project Structure (Day 3)

```
app/
├── core/
│   └── exceptions.py       # Custom exception classes
├── routers/
│   └── posts.py            # Post endpoints
├── database/
│   └── posts_model.py      # Post data model
├── services/
│   └── db_handler.py       # Database operations
└── main.py                 # App entry point + exception handlers
```

---

### Endpoints Available

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/v1` | API version info |
| GET | `/api/v1/posts` | Get all posts |
| GET | `/api/v1/posts/{id}` | Get post by ID |
| POST | `/api/v1/posts` | Create a new post |
| PATCH | `/api/v1/posts/{id}` | Update a post |
| DELETE | `/api/v1/posts/{id}` | Delete a post |

---

### Tests Done Manually

| Scenario | Expected | Result |
|---|---|---|
| `GET /api/v1/posts/999` (non-existent) | 404 JSON | ✅ |
| `GET /api/v1/posts/abc` (invalid type) | 422 JSON | ✅ |
| `GET /api/v1/test-500` (forced crash) | 500 JSON, no stack trace | ✅ |

---

### Key Takeaways

- Never return `null` from a route — always raise the right exception
- Never expose stack traces or internal field names to clients
- A `request_id` on every error makes debugging possible without leaking internals
- `RequestValidationError` and `HTTPException` are different — you need separate handlers for both
- `if user_id is not None` is safer than `if user_id` even when your IDs can't be zero — it makes intent explicit

---

*Built as part of a structured backend learning path — Month 1, Day 3.*


# Day 5 — Request Lifecycle + Middleware
### Instagram Clone | Month 1 Backend Skills

---

## What Was Built Today

### Project Structure
```
app/
├── middleware/
│   ├── __init__.py
│   ├── request_id.py       ← generates unique ID for every request
│   └── logging.py          ← logs every request with timing
├── dependencies/
│   └── auth.py             ← get_current_user() stub
└── main.py                 ← registers middleware + exception handlers
```

---

## Middleware 1 — `middleware/request_id.py`

Generates a unique `X-Request-ID` for every incoming request and attaches it to the response header.

**Key behaviour:**
- If the incoming request already has an `X-Request-ID` (e.g. from CDN or API Gateway), it reuses that ID — preserving the trace chain
- If no ID exists, it generates a new `uuid4()`
- Stores the ID in `request.state.request_id` so all other middleware and route handlers can access it

**Why this matters at Instagram scale:**
Every request that flows through CDN → API Gateway → Auth → your server needs a single traceable ID. Without it, engineers cannot find a specific failed request among billions of daily logs.

---

## Middleware 2 — `middleware/logging.py`

Logs every request with method, path, status code, and duration.

**Log format:**
```
2026-04-09 09:39:58 | INFO | req_id=a71807de-7ca6-4ef7-8a09-91f7d69e4569 | GET /api/v1/posts | 200 | 45ms
```

**Key behaviour:**
- Timer starts **before** `call_next` — captures full request duration
- Timer stops **after** `call_next` — status code and duration now available
- Reads `request_id` safely using `getattr(request.state, 'request_id', 'unknown')` — won't crash even if request_id middleware didn't run
- Logs to `app.log` file

**Why `perf_counter()` over `time.time()`:**
`perf_counter()` is a high-resolution timer designed for measuring short durations. `time.time()` can drift or have low resolution depending on the OS — not suitable for measuring millisecond-level endpoint performance.

---

## Middleware Registration Order — `main.py`

FastAPI executes middleware in **reverse registration order**. So to run `request_id` first and `logging` second:

```python
# Register logging first (runs second)
app.middleware("http")(log_request)

# Register request_id second (runs first)
app.middleware("http")(add_request_id_to_header)
```

**Execution flow:**
```
Incoming Request
      ↓
add_request_id_to_header   ← assigns request_id
      ↓
log_request                ← reads request_id, starts timer
      ↓
Route Handler
      ↓
log_request                ← stops timer, logs everything
      ↓
add_request_id_to_header   ← attaches X-Request-ID to response header
      ↓
Outgoing Response
```

---

## Dependency Stub — `dependencies/auth.py`

A placeholder `get_current_user()` function using FastAPI's `Depends()` system.

**Returns a dummy user for now:**
```python
{
    "user_id": "test_user_id",
    "username": "test_user"
}
```

Returns a plain dictionary — not a `JSONResponse`. The route handler is responsible for building the response, not the dependency function.

**Will be replaced later** with real JWT token validation and database lookup.

---

## Exception Handling — `main.py`

All exception handlers include `request_id` in the error response so clients can report it and engineers can trace it in logs.

**Helper function to avoid repetition:**
```python
def get_request_id(request):
    return getattr(request.state, 'request_id', 'unknown')
```

**Handled exceptions:**
| Exception | Status Code |
|-----------|-------------|
| `PostNotFound` | 404 |
| `UserNotFound` | 404 |
| `NotAuthorized` | 401/403 |
| `HTTPException` | varies |
| `RequestValidationError` | 422 |
| `Exception` (generic) | 500 |

---

## Key Concepts Learned

**Middleware execution flow:**
```
Request → [Middleware] → Route Handler → [Middleware] → Response
```

**Instagram's real middleware stack at API Gateway:**
1. TLS termination
2. DDoS protection
3. Auth token validation
4. Rate limiting
5. Request routing

Today's middleware simulates layers 4 and 5 at a small scale.

**Why `@app.middleware("http")` over `BaseHTTPMiddleware`:**
`BaseHTTPMiddleware` has known performance issues under load and does not work well with background tasks. The `@app.middleware("http")` decorator is preferred in production FastAPI applications.

**P50 / P95 / P99 latency:**
Instagram tracks what percentage of requests complete within a given time. If P99 for an endpoint is too high, engineers investigate and optimize that specific endpoint.

**Correlation IDs:**
Every request gets a unique ID that appears in every log line. When a user reports a problem, engineers search logs by that ID and trace the exact failure point across all microservices instantly.

---

## Logging Configuration

Configured in `main.py` — not inside individual middleware files:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="app.log"
)
```

---

## Day Deliverable

Every request is now:
- Assigned a unique `X-Request-ID`
- Logged with method, path, status code, and duration
- Traceable across the entire application via `request.state.request_id`
- Included in every error response for client-side reporting