from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import SessionLocal

router = APIRouter(tags=["Masking"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/masking", response_model=schemas.MaskingOut)
def save_masking(payload: schemas.MaskingCreate, db: Session = Depends(get_db)):
    record = models.MaskingSettings(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/masking/recent", response_model=list[schemas.MaskingOut])
def recent_masking(db: Session = Depends(get_db)):
    return db.query(models.MaskingSettings).order_by(models.MaskingSettings.id.desc()).limit(50).all()