from fastapi import FastAPI
from .database import engine, Base
from .api import api_sessions, api_configs, api_uploadstep1

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(api_sessions.router)
app.include_router(api_configs.router)
app.include_router(api_uploadstep1.router)

@app.get("/")
def read_root():
    return {"status": "ok"}
