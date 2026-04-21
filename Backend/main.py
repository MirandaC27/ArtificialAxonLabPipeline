from fastapi import FastAPI
from .database import engine, Base
from . import api_sum 
from . import api_name
from . import api_upload_settings

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(api_sum.router)
app.include_router(api_name.router)
app.include_router(api_upload_settings.router)

@app.get("/")
def read_root():
    return {"status": "ok"}
