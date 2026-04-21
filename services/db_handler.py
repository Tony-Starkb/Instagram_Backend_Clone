import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

import bcrypt


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_AVATAR_URL = "https://example.com/default-avatar.png"
DATA_LOCK = Lock()

USERS_FILE = Path(os.getenv("USERS_FILE_PATH", BASE_DIR / "schemas" / "users.json"))
POSTS_FILE = Path(os.getenv("POSTS_FILE_PATH", BASE_DIR / "schemas" / "posts.json"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(file_path: Path, data):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=file_path.parent, encoding="utf-8") as temp_file:
        json.dump(data, temp_file, indent=4)
        temp_name = temp_file.name
    Path(temp_name).replace(file_path)


def _hash_legacy_password(raw_value: str) -> str:
    if raw_value.startswith("$2"):
        return raw_value
    if raw_value.startswith("hash_"):
        raw_value = raw_value.removeprefix("hash_")
    return bcrypt.hashpw(raw_value.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _normalize_user(user: dict) -> dict:
    normalized = dict(user)
    normalized["id"] = str(normalized["id"])
    normalized["email"] = str(normalized["email"]).lower()
    normalized["username"] = str(normalized["username"])
    normalized["full_name"] = normalized.get("full_name") or normalized["username"]
    normalized["bio"] = normalized.get("bio") or ""
    normalized["avatar_url"] = normalized.get("avatar_url") or DEFAULT_AVATAR_URL
    normalized["is_private"] = bool(normalized.get("is_private", False))
    normalized["is_verified"] = bool(normalized.get("is_verified", False))
    normalized["role"] = normalized.get("role") or "user"
    normalized["followers"] = list(normalized.get("followers", []))
    normalized["following"] = list(normalized.get("following", []))
    normalized["created_at"] = normalized.get("created_at") or _now_iso()
    normalized["password_hash"] = _hash_legacy_password(str(normalized["password_hash"]))
    return normalized


LEGACY_POST_USERNAMES = {
    "tony": "tony_123",
    "steve": "steve-rogers",
}


def _normalize_post(post: dict) -> dict:
    normalized = dict(post)
    normalized["id"] = int(normalized["id"])
    normalized["username"] = LEGACY_POST_USERNAMES.get(normalized.get("username"), normalized.get("username"))
    normalized["caption"] = normalized.get("caption") or ""
    normalized["image_url"] = str(normalized["image_url"])
    normalized["liked_by"] = list(normalized.get("liked_by", []))
    normalized["like_count"] = int(normalized.get("like_count", len(normalized["liked_by"])))
    normalized["comment_count"] = int(normalized.get("comment_count", 0))
    normalized["created_at"] = normalized.get("created_at") or _now_iso()
    normalized["updated_at"] = normalized.get("updated_at")
    return normalized


def _load_users() -> list[dict]:
    with DATA_LOCK:
        users = [_normalize_user(user) for user in _read_json(USERS_FILE)]
        _write_json(USERS_FILE, users)
        return users


def _save_users(users: list[dict]) -> None:
    with DATA_LOCK:
        _write_json(USERS_FILE, users)


def _load_posts() -> list[dict]:
    with DATA_LOCK:
        posts = [_normalize_post(post) for post in _read_json(POSTS_FILE)]
        _write_json(POSTS_FILE, posts)
        return posts


def _save_posts(posts: list[dict]) -> None:
    with DATA_LOCK:
        _write_json(POSTS_FILE, posts)


def _public_user(user: dict) -> dict:
    posts = get_user_posts(user["username"])
    return {
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "bio": user["bio"],
        "avatar_url": user["avatar_url"],
        "is_private": user["is_private"],
        "is_verified": user["is_verified"],
        "follower_count": len(user["followers"]),
        "following_count": len(user["following"]),
        "post_count": len(posts),
        "created_at": user["created_at"],
    }


def get_all_users() -> list[dict]:
    return [_public_user(user) for user in _load_users()]


def get_user_by_id(user_id: str):
    for user in _load_users():
        if user["id"] == str(user_id):
            return user
    return None


def get_user_by_username(username: str):
    for user in _load_users():
        if user["username"].lower() == username.lower():
            return user
    return None


def get_user_by_email(email: str):
    for user in _load_users():
        if user["email"] == str(email).lower():
            return user
    return None


def add_user(user: dict) -> dict:
    users = _load_users()
    normalized_user = _normalize_user(user)
    users.append(normalized_user)
    _save_users(users)
    return normalized_user


def get_public_user(username: str):
    user = get_user_by_username(username)
    if user is None:
        return None
    return _public_user(user)


def get_all_posts() -> list[dict]:
    return sorted(_load_posts(), key=lambda item: item["created_at"], reverse=True)


def get_post_by_id(post_id: int):
    for post in _load_posts():
        if post["id"] == int(post_id):
            return post
    return None


def get_user_posts(username: str) -> list[dict]:
    target_username = str(username).lower()
    return [post for post in get_all_posts() if post["username"].lower() == target_username]


def add_post(post: dict) -> dict:
    posts = _load_posts()
    next_id = max((item["id"] for item in posts), default=0) + 1
    normalized_post = _normalize_post(
        {
            "id": next_id,
            "username": post["username"],
            "caption": post["caption"],
            "image_url": post["image_url"],
            "like_count": 0,
            "comment_count": 0,
            "liked_by": [],
            "created_at": _now_iso(),
            "updated_at": None,
        }
    )
    posts.append(normalized_post)
    _save_posts(posts)
    return normalized_post


def update_post(post_id: int, updates: dict):
    posts = _load_posts()
    for index, post in enumerate(posts):
        if post["id"] == int(post_id):
            updated_post = dict(post)
            updated_post.update({key: value for key, value in updates.items() if value is not None})
            updated_post["updated_at"] = _now_iso()
            posts[index] = _normalize_post(updated_post)
            _save_posts(posts)
            return posts[index]
    return None


def delete_post(post_id: int) -> bool:
    posts = _load_posts()
    filtered_posts = [post for post in posts if post["id"] != int(post_id)]
    if len(filtered_posts) == len(posts):
        return False
    _save_posts(filtered_posts)
    return True


def like_post(post_id: int, username: str):
    posts = _load_posts()
    for index, post in enumerate(posts):
        if post["id"] == int(post_id):
            if username in post["liked_by"]:
                return "already-liked", post
            updated_post = dict(post)
            updated_post["liked_by"] = [*post["liked_by"], username]
            updated_post["like_count"] = len(updated_post["liked_by"])
            updated_post["updated_at"] = _now_iso()
            posts[index] = _normalize_post(updated_post)
            _save_posts(posts)
            return "liked", posts[index]
    return "missing", None


def unlike_post(post_id: int, username: str):
    posts = _load_posts()
    for index, post in enumerate(posts):
        if post["id"] == int(post_id):
            if username not in post["liked_by"]:
                return "not-liked", post
            updated_post = dict(post)
            updated_post["liked_by"] = [item for item in post["liked_by"] if item != username]
            updated_post["like_count"] = len(updated_post["liked_by"])
            updated_post["updated_at"] = _now_iso()
            posts[index] = _normalize_post(updated_post)
            _save_posts(posts)
            return "unliked", posts[index]
    return "missing", None
