from fastapi import FastAPI
import uvicorn
from app.api import router

app = FastAPI()

app.include_router(router)
