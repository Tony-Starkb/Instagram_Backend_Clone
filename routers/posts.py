from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
import uuid


router = APIRouter()


@router.get("/posts", status_code = status.HTTP_200_OK)
def get_post(request: Request):

	print(dict(request.headers))

	response = JSONResponse(
			{"message": "required post send"}
		)
	response.headers["X-Request-ID"] = str(uuid.uuid4())
	return response

@router.post("/posts", status_code = status.HTTP_201_CREATED)
def create_post(request: Request):

	print(dict(request.headers))

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