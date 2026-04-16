from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from services import db_handler
from schemas.post import PostCreate, PostResponse
from core.exceptions import PostNotFound


posts_router = APIRouter(prefix = "/api/v1/posts", tags = ["posts"])


@posts_router.get("/{id}", status_code = status.HTTP_200_OK)
def get_post_by_id(id: int, request: Request):
	
	print(dict(request.headers))
	db_post = db_handler.get_post_by_id(id)
	if db_post is None:
		raise PostNotFound(id)

	response = JSONResponse(
			db_post
		)

	return response



@posts_router.post("/", status_code = status.HTTP_201_CREATED)
def create_post(request: Request, post: PostCreate):

	print(dict(request.headers))
	db_handler.add_post(post.model_dump())

	response = JSONResponse(
			{"message": "post created"}
		)

	
	return response



@posts_router.delete("/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_post(id: int, request: Request):
	
	print(dict(request.headers))

	return None


@posts_router.patch("/{id}", status_code = status.HTTP_200_OK)
def update_specific_part_of_post(id: int, request: Request):
	
	print(dict(request.headers))

	response = JSONResponse(
			{"message": "updated successfully"}
		)

	
	return response


@posts_router.post("/{id}/like", status_code = status.HTTP_200_OK)
def like_post(id: int, request: Request):
    print(dict(request.headers))

    response = JSONResponse(
            {"message": "post liked"}
    )
    return response
	

@posts_router.delete("/{id}/like", status_code = status.HTTP_204_NO_CONTENT)
def unlike_post(id: int, request: Request):
	print(dict(request.headers))

