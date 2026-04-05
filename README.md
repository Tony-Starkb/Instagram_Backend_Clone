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
