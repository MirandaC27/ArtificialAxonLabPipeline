from fastapi import FastAPI
from .database import engine, Base
from . import api_sum

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(api_sum.router)

@app.get("/")
def read_root():
    return {"status": "ok"}
