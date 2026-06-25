from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from ..database import SessionLocal
from .. import models
from .. import schemas


router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.post(
    "/upload-step1",
    response_model=schemas.Step1Out
)
def save_upload(
    payload: schemas.Step1Create,
    db: Session = Depends(get_db)
):

    record = models.UploadStep1(
        **payload.model_dump()
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get(
    "/upload-step1/recent",
    response_model=list[schemas.Step1Out]
)
def recent_uploads(
    db: Session = Depends(get_db)
):
    return (
        db.query(models.UploadStep1)
        .order_by(models.UploadStep1.id.desc())
        .limit(50)
        .all()
    )