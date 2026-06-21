from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.schemas import PostCreate, PostUpdate, PostResponse
from core.exceptions import PostNotFound
from services.dependencies import get_current_user, get_db
from database.crud import add_post as crud_add_post, delete_post as crud_delete_post, get_post_by_id as crud_get_post_by_id, update_post as crud_update_post, like_post as crud_like_post, unlike_post as crud_unlike_post


posts_router = APIRouter(prefix = "/api/v1/posts", tags = ["posts"])

"""
@posts_router.get(
    "", 
    status_code=status.HTTP_200_OK, 
    response_model=list[PostResponse]
)
def get_all_posts(
    current_user = Depends(get_current_user)  # handles 401 internally
):
    return db_handler.get_all_posts()
"""


@posts_router.get("/{id}", status_code = status.HTTP_200_OK, response_model=PostResponse)
def get_post_by_id(id: str, request: Request, db: Session = Depends(get_db)):
	db_post = crud_get_post_by_id(db, id)
	if db_post is None:
		raise PostNotFound(id)
	return db_post



@posts_router.post("/", status_code = status.HTTP_201_CREATED, response_model=PostResponse)
def create_post(
    post: PostCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    
    created_post = crud_add_post(db, post, current_user.id, current_user.username)
    return created_post



@posts_router.delete("/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_post(
    id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    post = crud_get_post_by_id(db, id)
    if post is None:
        raise PostNotFound(id)
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own posts.")
    if not crud_delete_post(db, id):
        raise PostNotFound(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@posts_router.patch("/{id}", status_code = status.HTTP_200_OK, response_model=PostResponse)
def update_specific_part_of_post(
    id: str,
    request: Request,
    updates: PostUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
	post = crud_get_post_by_id(db, id)
	if post is None:
		raise PostNotFound(id)
	if post.user_id != current_user.id:
		raise HTTPException(status_code=403, detail="You can only update your own posts.")
	updated_post = crud_update_post(db, id, updates)
	if updated_post is None:
		raise PostNotFound(id)
	return updated_post


@posts_router.post("/{id}/like", status_code = status.HTTP_200_OK)
def like_post(
    id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    status_name, post = crud_like_post(db, id, current_user.id)
    if status_name == "missing":
        raise PostNotFound(id)
    if status_name == "already-liked":
        raise HTTPException(status_code=409, detail="You have already liked this post.")
    return {"message": "Post liked.", "post likes": post.like_count}
	

@posts_router.delete("/{id}/like", status_code = status.HTTP_204_NO_CONTENT)
def unlike_post(
    id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
	status_name, post = crud_unlike_post(db, id, current_user.id)
	if status_name == "missing":
		raise PostNotFound(id)
	if status_name == "not-liked":
		raise HTTPException(status_code=409, detail="You have not liked this post.")
	return Response(status_code=status.HTTP_204_NO_CONTENT)


