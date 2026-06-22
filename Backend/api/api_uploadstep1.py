from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import SessionLocal
from .. import models, schemas

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload-step1", response_model=schemas.UploadStep1Out)
def save_upload_step1(
    upload: schemas.UploadStep1Create,
    db: Session = Depends(get_db)
):
    record = models.UploadStep1(
        folders=upload.folders,
        tracks=upload.tracks,
        tracks1=upload.tracks1,
        ordered_track=upload.ordered_track,
        data=upload.data,
        image_type=upload.image_type,
        microscope=upload.microscope,
        num_fovs=upload.num_fovs,
        disabled_fovs=upload.disabled_fovs,
        channels=upload.channels,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get("/upload-step1/recent", response_model=list[schemas.UploadStep1Out])
def get_recent_upload_step1(db: Session = Depends(get_db)):
    return (
        db.query(models.UploadStep1)
        .order_by(models.UploadStep1.id.desc())
        .limit(10)
        .all()
    )