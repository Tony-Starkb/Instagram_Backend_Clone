import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from core.exceptions import PostNotFound, UserNotFound, NotAuthorized
from middleware.logging import log_request
from middleware.request_id import add_request_id_to_header
from routers.auth import auth_router as login_router
from routers.posts import posts_router as post_router
from routers.users import users_router as user_router


logging.basicConfig(
	level = logging.INFO,
	format = "%(asctime)s | %(levelname)s | %(message)s",
	datefmt = "%Y-%m-%d %H:%M:%S",
	filename = "app.log"
) 

logger = logging.getLogger(__name__)


def build_error_response(request: Request, status_code: int, message: str):
    request_id = getattr(request.state, 'request_id', 'unknown')
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": status_code,
                "message": message,
                "request_id": request_id
            }
        },
        headers={"X-Request-ID": request_id},
    )


app = FastAPI()


# Middleware: Add request ID first, then logging
app.middleware("http")(log_request)
app.middleware("http")(add_request_id_to_header)


@app.get("/health")
def check_health():
	return JSONResponse({"status": "ok"})


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
    return build_error_response(request, exc.status_code, exc.detail)

@app.exception_handler(UserNotFound)
def user_not_found_handler(request: Request, exc: UserNotFound):
    return build_error_response(request, exc.status_code, exc.detail)

@app.exception_handler(NotAuthorized)
def not_authorized_handler(request: Request, exc: NotAuthorized):
    return build_error_response(request, exc.status_code, exc.detail)
    
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for request_id=%s", getattr(request.state, "request_id", "unknown"))
    return build_error_response(request, 500, "Internal server error.")
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return build_error_response(request, 422, "Validation failed.")
      
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return build_error_response(request, exc.status_code, exc.detail)
