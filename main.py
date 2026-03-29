from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routers.posts import router as post_router


app = FastAPI()


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


app.include_router(post_router, prefix = "/api/v1")