from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from database.crud import get_post_by_id, delete_post, get_user_by_id
from database.schemas import UserPublicResponse
from core.exceptions import PostNotFound
from services.dependencies import get_current_user, require_role
from services.dependencies import get_db
from sqlalchemy.orm import Session


moderate_router = APIRouter(prefix="/api/v1/moderate", tags=["Moderator/Admin"])


@moderate_router.delete(
    "/posts/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def moderator_delete_post(
    id: str,
    current_user: dict = Depends(require_role({"admin", "moderator"})),
    db: Session = Depends(get_db)
):
    post = get_post_by_id(db, id)
    
    if post is None:
        raise PostNotFound(id)
    
    if not delete_post(db, id):
        raise PostNotFound(id)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    

# this endpoint till become useful when I update the project in which i will give the 
# normal user the ability to choose wether it account should be private or public
# and the admin and the moderator can see both type of accounts
@moderate_router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK
)
def moderate_get_user_profile(
    user_id: str,
    current_user: dict = Depends(require_role({"admin", "moderator"})),
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    return UserPublicResponse.model_validate(user)
        