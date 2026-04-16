
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routers.posts import posts_router as post_router
from routers.users import users_router as user_router
from routers.auth import auth_router as login_router
from fastapi.exceptions import HTTPException, RequestValidationError
from core.exceptions import PostNotFound, UserNotFound, NotAuthorized
import logging
from middleware.request_id import add_request_id_to_header
from middleware.logging import log_request


logging.basicConfig(
	level = logging.INFO,
	format = "%(asctime)s | %(levelname)s | %(message)s",
	datefmt = "%Y-%m-%d %H:%M:%S",
	filename = "app.log"
) 

def get_request_id(request, exc):
    status_code = getattr(exc, "status_code", 500)
    message = getattr(exc, "detail", str(exc))

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": status_code,
                "message": message,
                "request_id": getattr(request.state, 'request_id', 'unknown')
            }
        }
    )


app = FastAPI()


# Middleware: Add request ID first, then logging
app.middleware("http")(log_request)
app.middleware("http")(add_request_id_to_header)


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
app.include_router(login_router)


@app.exception_handler(PostNotFound)
def post_not_found_handler(request: Request, exc: PostNotFound):
    response = get_request_id(request, exc)
    return response

@app.exception_handler(UserNotFound)
def user_not_found_handler(request: Request, exc: UserNotFound):
    response = get_request_id(request, exc)
    return response

@app.exception_handler(NotAuthorized)
def not_authorized_handler(request: Request, exc: NotAuthorized):
    response = get_request_id(request, exc)
    return response		

@app.exception_handler(NotAuthorized)
def not_authorized_handler(request: Request, exc: NotAuthorized):
    response = get_request_id(request, exc)
    return response
    
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    response = get_request_id(request, exc)
    return response
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    response = get_request_id(request, exc)
    return response
      
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    response = get_request_id(request, exc)
    return response