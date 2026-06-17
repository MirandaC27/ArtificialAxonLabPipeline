from fastapi import FastAPI
from .database import engine, Base
from .api import api_name, api_sum, api_sessions, api_configs

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(api_sum.router)
app.include_router(api_name.router)
app.include_router(api_sessions.router)
app.include_router(api_configs.router)

@app.get("/")
def read_root():
    return {"status": "ok"}
