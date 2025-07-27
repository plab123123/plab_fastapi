from fastapi import FastAPI
from app.routers import analyze

app = FastAPI()
app.include_router(analyze.router)
