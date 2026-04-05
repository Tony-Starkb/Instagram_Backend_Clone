from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from services import db_handler
#from database.users_model import Users
from core.exceptions import UserNotFound, PostNotFound


users_router = APIRouter(prefix = "/api/v1/users")


@users_router.get("/{username}", status_code = status.HTTP_200_OK)
def get_user_by_username(username: str, request: Request):
    print(dict(request.headers))
    
    db_user = db_handler.get_user_by_username(username)
    if db_user is None:
        raise UserNotFound(username)

    response = JSONResponse(
        db_user
    )
    
    return response



@users_router.get("/{username}/posts", status_code = status.HTTP_200_OK)
def get_users_posts(username: str, request: Request):
    print(dict(request.headers))
    
    db_user = db_handler.get_user_by_username(username)
    if db_user is None:
        raise UserNotFound(username)
    
    db_user_posts = db_handler.get_user_posts(username)
    
    response = JSONResponse(
        db_user_posts
    )
    
    return response
    
    
@users_router.get("/{username}/followers", status_code = status.HTTP_200_OK)
def get_user_followers(username: str, request: Request):
    print(dict(request.headers))
    return JSONResponse(
        {"message": f"followers of {username}"}
    )
    
@users_router.get("/{username}/following", status_code = status.HTTP_200_OK)
def get_user_following(username: str, request: Request):
    print(dict(request.headers))
    return JSONResponse(
        {"message": f"users followed by {username}"}
    )
