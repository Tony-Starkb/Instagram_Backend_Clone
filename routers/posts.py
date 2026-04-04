from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
import uuid
from services import db_handler
from database.posts_model import Posts
from core.exceptions import PostNotFound


router = APIRouter()


# to fetch all the posts available in database
@router.get("/posts", status_code = status.HTTP_200_OK)
def get_post(request: Request):

	print(dict(request.headers))
	#return db_handler.get_all_posts()


	response = JSONResponse(
			db_handler.get_all_posts()
		)
	response.headers["X-Request-ID"] = str(uuid.uuid4())
	return response


@router.get("/posts/{id}", status_code = status.HTTP_200_OK)
def get_post_by_id(id: int, request: Request):
	
	print(dict(request.headers))
	#return db_handler.get_post_by_id(id)

	response = JSONResponse(
			db_handler.get_post_by_id(id)
		)
	response.headers["X-Request-ID"] = str(uuid.uuid4())
	if response.body == b'null':
		raise PostNotFound(id)
	return response



@router.post("/posts", status_code = status.HTTP_201_CREATED)
def create_post(request: Request, post: Posts):

	print(dict(request.headers))
	db_handler.add_post(post)

	response = JSONResponse(
			{"message": "post created"}
		)

	response.headers["X-Request-ID"] = str(uuid.uuid4())
	return response



@router.delete("/posts/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_post(id: int, request: Request):
	
	print(dict(request.headers))

	return None


@router.patch("/posts/{id}", status_code = status.HTTP_200_OK)
def update_specific_part_of_post(id: int, request: Request):
	
	print(dict(request.headers))

	response = JSONResponse(
			{"message": "updated successfully"}
		)

	response.headers["X-Request-ID"] = str(uuid.uuid4())
	return response