from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import SessionLocal
from ..scripts.analysis.pipeline_runner import build_final_csv


router = APIRouter(prefix="/analysis", tags=["Analysis"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_analysis_job(job_id):
    db = SessionLocal()
    try:
        job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == job_id).first()
        if not job:
            return
        job.status = "running"
        job.progress = 1
        job.progress_message = "Preparing analysis"
        db.commit()

        def report_progress(percent, message):
            progress_db = SessionLocal()
            try:
                progress_job = progress_db.query(models.AnalysisJob).filter(models.AnalysisJob.id == job_id).first()
                if progress_job:
                    progress_job.progress = max(0, min(99, int(percent)))
                    progress_job.progress_message = str(message)[:255]
                    progress_db.commit()
            finally:
                progress_db.close()

        csv_content, row_count = build_final_csv(job.payload, report_progress)
        filename = f"final_results_job_{job.id}.csv"
        result = models.ResultCsv(
            filename=filename,
            content=csv_content,
            order_index=db.query(models.ResultCsv).count(),
        )
        db.add(result)
        db.flush()
        job.status = "completed"
        job.result_id = result.id
        job.row_count = row_count
        job.error = None
        job.progress = 100
        job.progress_message = "Analysis complete"
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(exc)[-8000:]
            job.progress_message = "Analysis failed"
            db.commit()
    finally:
        db.close()


@router.post("/jobs", response_model=schemas.AnalysisJobOut)
def create_analysis_job(
    payload: schemas.AnalysisJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    active = db.query(models.AnalysisJob).filter(
        models.AnalysisJob.status.in_(["queued", "running"])
    ).first()
    if active:
        # The pipeline uses shared intermediate files, so reuse its one active
        # worker and let callers reconnect to it.
        return active
    job = models.AnalysisJob(status="queued", payload=payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(run_analysis_job, job.id)
    return job


@router.get("/jobs/{job_id}", response_model=schemas.AnalysisJobOut)
def get_analysis_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    return job
