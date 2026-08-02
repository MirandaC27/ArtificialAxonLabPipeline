from fastapi import FastAPI

from .database import engine
from .database import Base

from .api import api_uploadstep1
from .api import api_settings
from .api import api_configs
from .api import api_masking
from .api import api_results
from .api import api_analysis
from sqlalchemy import text


app = FastAPI(
    title="Artificial Axon Lab Pipeline API",
    openapi_tags=[
        {"name": "Upload", "description": "Upload workflow and session history."},
        {"name": "Settings", "description": "Experiment settings."},
        {"name": "Masking", "description": "Masking and threshold settings."},
        {"name": "Configs", "description": "Saved workflow configurations."},
        {"name": "Results", "description": "PostgreSQL-backed CSV results."},
        {"name": "Analysis", "description": "Docker-based ImageJ analysis jobs."},
        {"name": "Health", "description": "API availability checks."},
    ],
)

Base.metadata.create_all(bind=engine)


def add_workflow_json_columns():
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE upload_step1 ADD COLUMN IF NOT EXISTS masking_data JSON NOT NULL DEFAULT '{}'"))
        connection.execute(text("ALTER TABLE upload_configs ADD COLUMN IF NOT EXISTS masking_data JSON NOT NULL DEFAULT '{}'"))


def add_analysis_progress_columns():
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS progress INTEGER NOT NULL DEFAULT 0"))
        connection.execute(text("ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS progress_message VARCHAR(255)"))


add_workflow_json_columns()
add_analysis_progress_columns()


def fail_interrupted_analysis_jobs():
    """Release jobs whose in-process worker disappeared with the API."""
    db = api_analysis.SessionLocal()
    try:
        interrupted = db.query(api_analysis.models.AnalysisJob).filter(
            api_analysis.models.AnalysisJob.status.in_(["queued", "running"])
        ).all()
        for job in interrupted:
            job.status = "failed"
            job.error = (
                "Analysis was interrupted when the API container stopped. "
                "Select Run Analysis to start it again."
            )
        if interrupted:
            db.commit()
    finally:
        db.close()


fail_interrupted_analysis_jobs()

app.include_router(api_uploadstep1.router)
app.include_router(api_settings.router)
app.include_router(api_configs.router)
app.include_router(api_masking.router)
app.include_router(api_results.router)
app.include_router(api_analysis.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok"}
