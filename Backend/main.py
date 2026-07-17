from fastapi import FastAPI

from .database import engine
from .database import Base

from .api import api_uploadstep1
from .api import api_settings
from .api import api_configs


app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(api_uploadstep1.router)
app.include_router(api_settings.router)
app.include_router(api_configs.router)


@app.get("/")
def root():
    return {"status": "ok"}