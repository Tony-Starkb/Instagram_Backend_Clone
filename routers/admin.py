from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from database.crud import get_user_by_username, get_user_by_id, update_user_role, get_user_by_username, delete_user
from database.schemas import Role
from core.exceptions import PostNotFound, UserNotFound
from services.dependencies import get_current_user, require_role
from services.dependencies import get_db
from sqlalchemy.orm import Session


admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


# endpoint using which the only admin was able to change the role of the users 
@admin_router.put(
    "/users/{user_id}/role",
    status_code=status.HTTP_204_NO_CONTENT
)
def admin_change_user_role(
    user_id: str,
    role: Role,
    current_user: dict = Depends(require_role({"admin"})),
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    
    if user is None:
        raise UserNotFound(user_id)
    
    if not update_user_role(db, user_id, role.value):
        raise UserNotFound(user_id)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# endpoint using which only the admin can ban any type of user, only admin have the permission for this
@admin_router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def admin_ban_user(
    user_id: str,
    current_user: dict = Depends(require_role({"admin"})),
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    
    if user is None:
        raise UserNotFound(user_id)
    if not delete_user(db, user_id):
        raise UserNotFound(user_id)
    
    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
    
    