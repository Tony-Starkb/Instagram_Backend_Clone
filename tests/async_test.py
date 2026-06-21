from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio


class EchoData(BaseModel):
    name: str
    age: int
    description: str = None


app = FastAPI()

@app.get("/health", status_code=200)
async def health_check():
    await asyncio.sleep(1)  # Simulate some async work
    return JSONResponse({"status": "ok"})
    
    
@app.post("/echo", status_code=200)
async def echo(data: EchoData):
    await asyncio.sleep(1)  # Simulate some async work
    return JSONResponse(data.dict())