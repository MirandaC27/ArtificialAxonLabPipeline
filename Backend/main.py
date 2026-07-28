from fastapi import FastAPI

from .database import engine
from .database import Base

from .api import api_uploadstep1
from .api import api_settings
from .api import api_configs
from .api import api_masking
from sqlalchemy import text


app = FastAPI()

Base.metadata.create_all(bind=engine)


def add_workflow_json_columns():
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE upload_step1 ADD COLUMN IF NOT EXISTS masking_data JSON NOT NULL DEFAULT '{}'"))
        connection.execute(text("ALTER TABLE upload_configs ADD COLUMN IF NOT EXISTS masking_data JSON NOT NULL DEFAULT '{}'"))


add_workflow_json_columns()

app.include_router(api_uploadstep1.router)
app.include_router(api_settings.router)
app.include_router(api_configs.router)
app.include_router(api_masking.router)


@app.get("/")
def root():
    return {"status": "ok"}