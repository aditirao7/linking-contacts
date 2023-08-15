from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models import SessionLocal, Contact

app = FastAPI()

db = SessionLocal()


@ app.get("/")
async def root():
    return {"message": "Hello World"}
