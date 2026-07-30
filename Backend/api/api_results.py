import base64
import binascii

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import SessionLocal


router = APIRouter(prefix="/results", tags=["results"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def serialize_result(record, include_content=False):
    result = {
        "id": record.id,
        "filename": record.filename,
        "order_index": record.order_index,
        "created_at": record.created_at,
    }
    if include_content:
        result["content_base64"] = base64.b64encode(record.content).decode("ascii")
    return result


@router.post("", response_model=schemas.ResultCsvOut)
def save_result(payload: schemas.ResultCsvCreate, db: Session = Depends(get_db)):
    filename = payload.filename.strip()
    if not filename or not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A .csv filename is required.")
    try:
        content = base64.b64decode(payload.content_base64, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=400, detail="Invalid CSV content.") from exc

    existing = db.query(models.ResultCsv).filter(models.ResultCsv.filename == filename).first()
    if existing:
        if not payload.overwrite:
            raise HTTPException(status_code=409, detail="A CSV with this name already exists.")
        existing.content = content
        record = existing
    else:
        record = models.ResultCsv(
            filename=filename,
            content=content,
            order_index=db.query(models.ResultCsv).count(),
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return serialize_result(record)


@router.get("", response_model=list[schemas.ResultCsvOut])
def list_results(db: Session = Depends(get_db)):
    records = db.query(models.ResultCsv).order_by(models.ResultCsv.order_index, models.ResultCsv.id).all()
    return [serialize_result(record) for record in records]


@router.get("/{result_id}", response_model=schemas.ResultCsvContent)
def get_result(result_id: int, db: Session = Depends(get_db)):
    record = db.query(models.ResultCsv).filter(models.ResultCsv.id == result_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="CSV not found.")
    return serialize_result(record, include_content=True)


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result(result_id: int, db: Session = Depends(get_db)):
    record = db.query(models.ResultCsv).filter(models.ResultCsv.id == result_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="CSV not found.")
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reorder/all")
def reorder_results(ids: list[int], db: Session = Depends(get_db)):
    records = db.query(models.ResultCsv).all()
    by_id = {record.id: record for record in records}
    if len(ids) != len(records) or set(ids) != set(by_id):
        raise HTTPException(status_code=400, detail="Reorder IDs must include every stored CSV exactly once.")
    for index, result_id in enumerate(ids):
        by_id[result_id].order_index = index
    db.commit()
    return {"status": "ok"}