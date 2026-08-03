import base64
import binascii
import re

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import SessionLocal


router = APIRouter(prefix="/results", tags=["Results"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def experiment_from_job(record, db):
    if not record.job_id:
        return None
    job = db.query(models.AnalysisJob).filter(
        models.AnalysisJob.id == record.job_id
    ).first()
    if not job:
        return None
    payload = job.payload or {}
    upload = payload.get("upload_data") or {}
    settings = payload.get("settings_data") or {}
    candidates = [settings.get("experiment")]
    for key in ("ordered_track", "tracks1", "tracks", "folders", "data"):
        value = upload.get(key) or []
        candidates.extend(value if isinstance(value, list) else [value])
    for value in candidates:
        match = re.search(
            r"(?<![A-Za-z0-9])EXP[\s_-]*0*([0-9]+)(?![0-9])",
            str(value or ""),
            re.IGNORECASE,
        )
        if match:
            return f"EXP{int(match.group(1)):03d}"
    return None


def serialize_result(record, db, include_content=False):
    result = {
        "id": record.id,
        "filename": record.filename,
        "mime_type": record.mime_type,
        "artifact_type": record.artifact_type,
        "job_id": record.job_id,
        "experiment": experiment_from_job(record, db),
        "order_index": record.order_index,
        "created_at": record.created_at,
    }
    if include_content:
        result["content_base64"] = base64.b64encode(record.content).decode("ascii")
    return result


@router.post("", response_model=schemas.ResultCsvOut)
def save_result(payload: schemas.ResultCsvCreate, db: Session = Depends(get_db)):
    filename = payload.filename.strip()
    if not filename:
        raise HTTPException(status_code=400, detail="A filename is required.")
    try:
        content = base64.b64decode(payload.content_base64, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=400, detail="Invalid artifact content.") from exc

    existing = db.query(models.ResultCsv).filter(models.ResultCsv.filename == filename).first()
    if existing:
        if not payload.overwrite:
            raise HTTPException(status_code=409, detail="An artifact with this name already exists.")
        existing.content = content
        existing.mime_type = payload.mime_type
        existing.artifact_type = payload.artifact_type
        existing.job_id = payload.job_id
        record = existing
    else:
        record = models.ResultCsv(
            filename=filename,
            content=content,
            mime_type=payload.mime_type,
            artifact_type=payload.artifact_type,
            job_id=payload.job_id,
            order_index=db.query(models.ResultCsv).count(),
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return serialize_result(record, db)


@router.get("", response_model=list[schemas.ResultCsvOut])
def list_results(db: Session = Depends(get_db)):
    records = db.query(models.ResultCsv).order_by(models.ResultCsv.order_index, models.ResultCsv.id).all()
    return [serialize_result(record, db) for record in records]


@router.get("/{result_id}", response_model=schemas.ResultCsvContent)
def get_result(result_id: int, db: Session = Depends(get_db)):
    record = db.query(models.ResultCsv).filter(models.ResultCsv.id == result_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return serialize_result(record, db, include_content=True)


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result(result_id: int, db: Session = Depends(get_db)):
    record = db.query(models.ResultCsv).filter(models.ResultCsv.id == result_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reorder/all")
def reorder_results(ids: list[int], db: Session = Depends(get_db)):
    records = db.query(models.ResultCsv).all()
    by_id = {record.id: record for record in records}
    if len(ids) != len(records) or set(ids) != set(by_id):
        raise HTTPException(status_code=400, detail="Reorder IDs must include every stored artifact exactly once.")
    for index, result_id in enumerate(ids):
        by_id[result_id].order_index = index
    db.commit()
    return {"status": "ok"}
