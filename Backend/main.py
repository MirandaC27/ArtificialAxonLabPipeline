from fastapi import FastAPI
from .database import engine, Base
from .api import api_sum 
from .api import api_name
from .api import api_upload_settings

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(api_sum.router)
app.include_router(api_name.router)
app.include_router(api_upload_settings.router)

@app.get("/")
def read_root():
    return {"status": "ok"}
