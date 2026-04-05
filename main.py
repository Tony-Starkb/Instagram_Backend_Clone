import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routers.posts import posts_router as post_router
from routers.users import users_router as user_router
from fastapi.exceptions import HTTPException, RequestValidationError
from core.exceptions import PostNotFound, UserNotFound, NotAuthorized


app = FastAPI()


@app.middleware("http")
async def update_header(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.get("/health")
def check_health():
	return JSONResponse(
		{
			"Status": "OK"
		}
	)


@app.get("/api/v1")
def version_info():
	return JSONResponse(
		{
			"version": "1.0.0",
			"name": "instagram_clone",
			"status": "running"
		}
	)


app.include_router(post_router)
app.include_router(user_router)

@app.exception_handler(PostNotFound)
def post_not_found_handler(request: Request, exc: PostNotFound):
    return JSONResponse(
		status_code=exc.status_code,
		content={
			"error": {
				"code": exc.status_code,
				"message": exc.detail,
				"request_id": request.state.request_id
			}
		}
	)

@app.exception_handler(UserNotFound)
def user_not_found_handler(request: Request, exc: UserNotFound):
    return JSONResponse(
		status_code=exc.status_code,
		content={
			"error": {
				"code": exc.status_code,
				"message": exc.detail,
    			"request_id": request.state.request_id
			}
		}
	)		

@app.exception_handler(NotAuthorized)
def not_authorized_handler(request: Request, exc: NotAuthorized):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "request_id": request.state.request_id
            }
        }
    )
    
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "request_id": request.state.request_id
            }
        }
    )
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	return JSONResponse(
		status_code=422,
		content={
			"error": {
				"code": 422,
				"message": "Validation error",
				"request_id": request.state.request_id
			}
		}
	)
      
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
		status_code=exc.status_code,
		content={
			"error": {
				"code": exc.status_code,
				"message": exc.detail,
				"request_id": request.state.request_id
			}
		}
	)