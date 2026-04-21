from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from services import db_handler
from schemas.user import UserPublicResponse
from core.exceptions import UserNotFound


users_router = APIRouter(prefix = "/api/v1/users", tags = ["users"])


@users_router.get("/{username}", status_code = status.HTTP_200_OK)
def get_user_by_username(username: str, request: Request):
    db_user = db_handler.get_public_user(username)
    if db_user is None:
        raise UserNotFound(username)
    return UserPublicResponse(**db_user).model_dump()



@users_router.get("/{username}/posts", status_code = status.HTTP_200_OK)
def get_users_posts(username: str, request: Request):
    db_user = db_handler.get_user_by_username(username)
    if db_user is None:
        raise UserNotFound(username)
    
    db_user_posts = db_handler.get_user_posts(username)
    return db_user_posts
    
    
@users_router.get("/{username}/followers", status_code = status.HTTP_200_OK)
def get_user_followers(username: str, request: Request):
    db_user = db_handler.get_user_by_username(username)
    if db_user is None:
        raise UserNotFound(username)
    return JSONResponse(
        {
            "username": username,
            "followers": db_user["followers"],
            "count": len(db_user["followers"]),
        }
    )
    
@users_router.get("/{username}/following", status_code = status.HTTP_200_OK)
def get_user_following(username: str, request: Request):
    db_user = db_handler.get_user_by_username(username)
    if db_user is None:
        raise UserNotFound(username)
    return JSONResponse(
        {
            "username": username,
            "following": db_user["following"],
            "count": len(db_user["following"]),
        }
    )
