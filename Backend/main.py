from fastapi import FastAPI

from .database import engine
from .database import Base

from .api import api_uploadstep1
from .api import api_settings
from .api import api_configs
from .api import api_masking
from .api import api_results
from sqlalchemy import text


app = FastAPI(
    title="Artificial Axon Lab Pipeline API",
    openapi_tags=[
        {"name": "Upload", "description": "Upload workflow and session history."},
        {"name": "Settings", "description": "Experiment settings."},
        {"name": "Masking", "description": "Masking and threshold settings."},
        {"name": "Configs", "description": "Saved workflow configurations."},
        {"name": "Results", "description": "PostgreSQL-backed CSV results."},
        {"name": "Health", "description": "API availability checks."},
    ],
)

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
app.include_router(api_results.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok"}