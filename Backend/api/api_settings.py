from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import SessionLocal
from .. import models, schemas


router = APIRouter(tags=["Settings"])


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/settings", response_model=schemas.SettingsOut)
def save_settings(
    payload: schemas.SettingsCreate,
    db: Session = Depends(get_db)
):
    record = models.UploadSettings(**payload.model_dump())

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get("/settings/recent", response_model=list[schemas.SettingsOut])
def recent_settings(db: Session = Depends(get_db)):
    return (
        db.query(models.UploadSettings)
        .order_by(models.UploadSettings.id.desc())
        .limit(50)
        .all()
    )