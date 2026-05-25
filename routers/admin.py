from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from services import db_handler
from schemas.user import Role
from core.exceptions import PostNotFound, UserNotFound
from services.dependencies import get_current_user, require_role


admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


# endpoint using which the only admin was able to change the role of the users 
@admin_router.put(
    "/users/{username}/role",
    status_code=status.HTTP_204_NO_CONTENT
)
def admin_change_user_role(
    username: str,
    role: Role,
    current_user: dict = Depends(require_role({"admin"}))
):
    user = db_handler.get_user_by_username(username)
    
    if user is None:
        raise UserNotFound(username)
    
    if not db_handler.update_user_role(username, role):
        raise UserNotFound(username)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# endpoint using which only the admin can ban any type of user, only admin have the permission for this
@admin_router.delete(
    "/users/{username}",
    status_code=status.HTTP_204_NO_CONTENT
)
def admin_ban_user(
    username: str,
    current_user: dict = Depends(require_role({"admin"}))
):
    user = db_handler.get_user_by_username(username)
    
    if user is None:
        raise UserNotFound(username)
    if not db_handler.delete_user(username):
        raise UserNotFound(username)
    
    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
    
    