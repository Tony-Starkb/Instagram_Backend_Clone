from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from services import db_handler
from schemas.post import PostCreate, PostResponse, PostUpdate
from core.exceptions import PostNotFound
from services.dependencies import get_current_user


posts_router = APIRouter(prefix = "/api/v1/posts", tags = ["posts"])


@posts_router.get("", status_code=status.HTTP_200_OK, response_model=list[PostResponse])
def get_all_posts(request: Request):
	return db_handler.get_all_posts()


@posts_router.get("/{id}", status_code = status.HTTP_200_OK)
def get_post_by_id(id: int, request: Request):
	db_post = db_handler.get_post_by_id(id)
	if db_post is None:
		raise PostNotFound(id)
	return db_post



@posts_router.post("/", status_code = status.HTTP_201_CREATED)
def create_post(
    request: Request,
    post: PostCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
	created_post = db_handler.add_post(
        {
            "username": current_user["username"],
            "caption": post.caption,
            "image_url": str(post.image_url),
        }
    )
	return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_post)



@posts_router.delete("/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_post(
    id: int,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
	post = db_handler.get_post_by_id(id)
	if post is None:
		raise PostNotFound(id)
	if post["username"] != current_user["username"]:
		raise HTTPException(status_code=403, detail="You can only delete your own posts.")
	if not db_handler.delete_post(id):
		raise PostNotFound(id)
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@posts_router.patch("/{id}", status_code = status.HTTP_200_OK)
def update_specific_part_of_post(
    id: int,
    request: Request,
    updates: PostUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
	post = db_handler.get_post_by_id(id)
	if post is None:
		raise PostNotFound(id)
	if post["username"] != current_user["username"]:
		raise HTTPException(status_code=403, detail="You can only update your own posts.")
	updated_post = db_handler.update_post(
        id,
        {
            "caption": updates.caption,
            "image_url": str(updates.image_url) if updates.image_url else None,
        },
    )
	return JSONResponse(updated_post)


@posts_router.post("/{id}/like", status_code = status.HTTP_200_OK)
def like_post(
    id: int,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    status_name, post = db_handler.like_post(id, current_user["username"])
    if status_name == "missing":
        raise PostNotFound(id)
    if status_name == "already-liked":
        raise HTTPException(status_code=409, detail="You have already liked this post.")
    return JSONResponse({"message": "Post liked.", "post": post})
	

@posts_router.delete("/{id}/like", status_code = status.HTTP_204_NO_CONTENT)
def unlike_post(
    id: int,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
	status_name, post = db_handler.unlike_post(id, current_user["username"])
	if status_name == "missing":
		raise PostNotFound(id)
	if status_name == "not-liked":
		raise HTTPException(status_code=409, detail="You have not liked this post.")
	return Response(status_code=status.HTTP_204_NO_CONTENT)

