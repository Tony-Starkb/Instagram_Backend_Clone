# Manual API Testing Guide

This guide helps you manually test every current endpoint in this project after any update.

## 1. Start the project

From `H:\Instagram_clone` run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Base URL:

```text
http://127.0.0.1:8000
```

You can also open Swagger UI in your browser:

```text
http://127.0.0.1:8000/docs
```

## 2. Test users you can use

These users are already present in `schemas/users.json` and are useful for manual testing:

- `tony_123` / `Tony@123`
- `steve-rogers` / `Steve@456`

Use `tony_123` as the post owner and `steve-rogers` as another user when testing permission and like/unlike flows.

## 3. Recommended test order

Run the scenarios in this order:

1. Health and version
2. Read-only user endpoints
3. Login
4. Create post
5. Read post
6. Update post
7. Like and unlike
8. Delete post
9. Validation and permission failure cases

## 4. PowerShell setup for authenticated requests

Login first and save the access token:

```powershell
$loginBody = "username=tony_123&password=Tony@123"
$loginResponse = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/auth/login" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body $loginBody

$token = $loginResponse.access_token
$authHeaders = @{ Authorization = "Bearer $token"; "X-Request-ID" = "manual-test-001" }
```

If you want a second user token:

```powershell
$loginBody2 = "username=steve-rogers&password=Steve@456"
$loginResponse2 = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/auth/login" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body $loginBody2

$token2 = $loginResponse2.access_token
$authHeaders2 = @{ Authorization = "Bearer $token2"; "X-Request-ID" = "manual-test-002" }
```

## 5. Endpoint-by-endpoint scenarios

### A. Health check

Endpoint:

```text
GET /health
```

Command:

```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/health"
```

Expected:

- Status `200`
- Body contains `{"status":"ok"}`

### B. API version

Endpoint:

```text
GET /api/v1
```

Command:

```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/v1"
```

Expected:

- Status `200`
- Response contains `version`, `name`, and `status`

### C. Get all posts

Endpoint:

```text
GET /api/v1/posts
```

Command:

```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/v1/posts"
```

Expected:

- Status `200`
- Response is an array
- Initially it should contain at least post IDs `1` and `2`

### D. Get post by valid ID

Endpoint:

```text
GET /api/v1/posts/1
```

Command:

```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/v1/posts/1"
```

Expected:

- Status `200`
- Response contains post data for ID `1`

### E. Get post by missing ID

Endpoint:

```text
GET /api/v1/posts/999
```

Command:

```powershell
try {
  Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/v1/posts/999"
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Expected:

- Status `404`
- Error message says the post was not found

### F. Get post with invalid ID type

Endpoint:

```text
GET /api/v1/posts/abc
```

Expected:

- Status `422`
- Error body uses the project’s structured error format

### G. Get user profile

Endpoint:

```text
GET /api/v1/users/tony_123
```

Command:

```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/v1/users/tony_123"
```

Expected:

- Status `200`
- Response contains `username`, `avatar_url`, `post_count`, `follower_count`, `following_count`

### H. Get missing user profile

Endpoint:

```text
GET /api/v1/users/missing_user
```

Expected:

- Status `404`
- Error message says the user was not found

### I. Get a user’s posts

Endpoint:

```text
GET /api/v1/users/tony_123/posts
```

Command:

```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/v1/users/tony_123/posts"
```

Expected:

- Status `200`
- Response is an array of posts created by `tony_123`

### J. Get followers

Endpoint:

```text
GET /api/v1/users/tony_123/followers
```

Expected:

- Status `200`
- Response contains `username`, `followers`, and `count`

### K. Get following

Endpoint:

```text
GET /api/v1/users/tony_123/following
```

Expected:

- Status `200`
- Response contains `username`, `following`, and `count`

### L. Login with valid credentials

Endpoint:

```text
POST /api/v1/auth/login
```

Command:

```powershell
Invoke-WebRequest -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/auth/login" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=tony_123&password=Tony@123"
```

Expected:

- Status `200`
- Body contains `access_token` and `token_type`
- Response headers include `Set-Cookie` with `refresh_token`

### M. Login with wrong password

Endpoint:

```text
POST /api/v1/auth/login
```

Command:

```powershell
try {
  Invoke-RestMethod -Method POST `
    -Uri "http://127.0.0.1:8000/api/v1/auth/login" `
    -ContentType "application/x-www-form-urlencoded" `
    -Body "username=tony_123&password=wrong-password"
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Expected:

- Status `401`
- Error message is `Invalid username or password`

### N. Register a new user

Endpoint:

```text
POST /api/v1/auth/registration
```

Command:

```powershell
$body = @{
  email = "manual_user_01@example.com"
  username = "manual_user_01"
  password = "Manual@123"
  full_name = "Manual User"
  bio = "created during manual testing"
  avatar_url = "https://example.com/manual-user.png"
} | ConvertTo-Json

Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/auth/registration" `
  -ContentType "application/json" `
  -Body $body
```

Expected:

- Status `201`
- Response contains `message`
- Response contains created user summary with `id`, `username`, and `email`

### O. Register with duplicate username

Use existing username `tony_123`.

Expected:

- Status `409`
- Error message says username already exists

### P. Register with duplicate email

Use existing email `tony.stark@example.com`.

Expected:

- Status `409`
- Error message says email already exists

### Q. Register with forbidden extra field

This project forbids extra fields in the request body.

Command:

```powershell
$body = @{
  email = "baduser@example.com"
  username = "bad_user_01"
  password = "BadUser@123"
  full_name = "Bad User"
  bio = "trying extra field"
  role = "super_admin"
} | ConvertTo-Json

try {
  Invoke-RestMethod -Method POST `
    -Uri "http://127.0.0.1:8000/api/v1/auth/registration" `
    -ContentType "application/json" `
    -Body $body
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Expected:

- Status `422`
- Error message is `Validation failed.`

### R. Create a post with authentication

Endpoint:

```text
POST /api/v1/posts/
```

Command:

```powershell
$newPost = @{
  caption = "Manual test post"
  image_url = "https://example.com/manual-post.png"
} | ConvertTo-Json

$createdPost = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/posts/" `
  -Headers $authHeaders `
  -ContentType "application/json" `
  -Body $newPost

$postId = $createdPost.id
$postId
```

Expected:

- Status `201`
- Post is created under logged-in user `tony_123`
- Save the returned `id` for later scenarios

### S. Create a post without token

Expected:

- Status `401`
- Error says credentials could not be validated or authentication is missing

### T. Create a post with invalid body

Example bad body:

```json
{
  "caption": "",
  "image_url": "not-a-url"
}
```

Expected:

- Status `422`

### U. Get the newly created post

Endpoint:

```text
GET /api/v1/posts/{postId}
```

Command:

```powershell
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/v1/posts/$postId"
```

Expected:

- Status `200`
- Returned ID matches the new post

### V. Update your own post

Endpoint:

```text
PATCH /api/v1/posts/{postId}
```

Command:

```powershell
$updateBody = @{
  caption = "Manual test post updated"
} | ConvertTo-Json

Invoke-RestMethod -Method PATCH `
  -Uri "http://127.0.0.1:8000/api/v1/posts/$postId" `
  -Headers $authHeaders `
  -ContentType "application/json" `
  -Body $updateBody
```

Expected:

- Status `200`
- Caption changes to `Manual test post updated`

### W. Update a post without token

Expected:

- Status `401`

### X. Update another user’s post

Login as `steve-rogers`, create a post with Tony, then try to update Tony’s post using Steve’s token:

```powershell
$steveUpdate = @{ caption = "Trying unauthorized update" } | ConvertTo-Json

try {
  Invoke-RestMethod -Method PATCH `
    -Uri "http://127.0.0.1:8000/api/v1/posts/$postId" `
    -Headers $authHeaders2 `
    -ContentType "application/json" `
    -Body $steveUpdate
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Expected:

- Status `403`
- Error message says you can only update your own posts

### Y. Like a post as another user

Endpoint:

```text
POST /api/v1/posts/{postId}/like
```

Command:

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/api/v1/posts/$postId/like" `
  -Headers $authHeaders2
```

Expected:

- Status `200`
- Message says `Post liked.`
- Returned post should show `like_count` increased

### Z. Like the same post again

Repeat the same request.

Expected:

- Status `409`
- Error says the post is already liked

### AA. Unlike the post

Endpoint:

```text
DELETE /api/v1/posts/{postId}/like
```

Command:

```powershell
Invoke-WebRequest -Method DELETE `
  -Uri "http://127.0.0.1:8000/api/v1/posts/$postId/like" `
  -Headers $authHeaders2
```

Expected:

- Status `204`
- No response body required

### AB. Unlike the same post again

Repeat the same request.

Expected:

- Status `409`
- Error says the post was not liked

### AC. Delete your own post

Endpoint:

```text
DELETE /api/v1/posts/{postId}
```

Command:

```powershell
Invoke-WebRequest -Method DELETE `
  -Uri "http://127.0.0.1:8000/api/v1/posts/$postId" `
  -Headers $authHeaders
```

Expected:

- Status `204`

### AD. Confirm deleted post is gone

Command:

```powershell
try {
  Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/api/v1/posts/$postId"
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Expected:

- Status `404`

### AE. Delete another user’s post

Create a fresh post as Tony, then try to delete it as Steve.

Expected:

- Status `403`
- Error says you can only delete your own posts

## 6. Full manual regression checklist

Use this checklist after every code update:

- `GET /health` returns `200`
- `GET /api/v1` returns `200`
- `GET /api/v1/posts` returns `200`
- `GET /api/v1/posts/1` returns `200`
- `GET /api/v1/posts/999` returns `404`
- `GET /api/v1/posts/abc` returns `422`
- `GET /api/v1/users/tony_123` returns `200`
- `GET /api/v1/users/missing_user` returns `404`
- `GET /api/v1/users/tony_123/posts` returns `200`
- `GET /api/v1/users/tony_123/followers` returns `200`
- `GET /api/v1/users/tony_123/following` returns `200`
- `POST /api/v1/auth/login` with valid credentials returns `200`
- `POST /api/v1/auth/login` with invalid credentials returns `401`
- `POST /api/v1/auth/registration` with valid new user returns `201`
- `POST /api/v1/auth/registration` with duplicate username returns `409`
- `POST /api/v1/auth/registration` with duplicate email returns `409`
- `POST /api/v1/auth/registration` with extra forbidden field returns `422`
- `POST /api/v1/posts/` with valid token returns `201`
- `POST /api/v1/posts/` without token returns `401`
- `PATCH /api/v1/posts/{id}` as owner returns `200`
- `PATCH /api/v1/posts/{id}` as another user returns `403`
- `POST /api/v1/posts/{id}/like` as another user returns `200`
- Duplicate like returns `409`
- `DELETE /api/v1/posts/{id}/like` returns `204`
- Duplicate unlike returns `409`
- `DELETE /api/v1/posts/{id}` as owner returns `204`
- `DELETE /api/v1/posts/{id}` as another user returns `403`

## 7. What to check in every error response

For all failure cases, verify:

- Response status code is correct
- Response body has an `error` object
- `error.code` matches the HTTP status
- `error.message` is human-readable
- `error.request_id` is present
- No Python traceback is leaked in the body

## 8. Important note about data files

This project stores data in JSON files, so manual testing changes the local data.

That means:

- newly registered users stay in `schemas/users.json`
- newly created posts affect `schemas/posts.json`
- likes and deletes also change those files

If you want a clean state before testing again, either restore those files manually or use a temporary copy approach like the automated tests in `tests/test_api.py`.
