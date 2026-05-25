from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from services import db_handler
from schemas.user import UserPublicResponse
from core.exceptions import PostNotFound
from services.dependencies import get_current_user, require_role


moderate_router = APIRouter(prefix="/api/v1/moderate", tags=["Moderator/Admin"])


@moderate_router.delete(
    "/posts/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def moderator_delete_post(
    id: int,
    current_user: dict = Depends(require_role({"admin", "moderator"}))
):
    post = db_handler.get_post_by_id(id)
    
    if post is None:
        raise PostNotFound(id)
    
    if not db_handler.delete_post(id):
        raise PostNotFound(id)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    

# this endpoint till become useful when I update the project in which i will give the 
# normal user the ability to choose wether it account should be private or public
# and the admin and the moderator can see both type of accounts
@moderate_router.get(
    "/{username}",
    status_code=status.HTTP_200_OK
)
def moderate_get_user_profile(
    username: str,
    current_user: dict = Depends(require_role({"admin", "moderator"}))
):
    user = db_handler.get_public_user(username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    return UserPublicResponse(**user)
        