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


def serialize_settings(settings):
    if not settings:
        return {}

    return {
        "experiment": settings.experiment,
        "frames": settings.frames,
        "distance": settings.distance,
        "run_ezra": settings.run_ezra,
    }


def normalize_settings(settings_data):
    if isinstance(settings_data, dict):
        return settings_data

    return {}


def settings_for_upload(upload, newer_upload, settings_records):
    upload_settings = normalize_settings(upload.settings_data)

    if upload_settings:
        return upload_settings

    upper_bound = newer_upload.created_at if newer_upload else None
    candidates = []

    for settings in settings_records:
        if settings.created_at < upload.created_at:
            continue

        if upper_bound and settings.created_at >= upper_bound:
            continue

        candidates.append(settings)

    if not candidates:
        return {}

    latest_settings = max(candidates, key=lambda item: item.created_at)
    return serialize_settings(latest_settings)


def serialize_upload(upload, settings_data=None):
    resolved_settings = normalize_settings(settings_data)

    if not resolved_settings:
        resolved_settings = normalize_settings(upload.settings_data)

    return {
        "id": upload.id,
        "created_at": upload.created_at,
        "folders": upload.folders,
        "tracks": upload.tracks,
        "tracks1": upload.tracks1,
        "ordered_track": upload.ordered_track,
        "data": upload.data,
        "image_type": upload.image_type,
        "microscope": upload.microscope,
        "num_fovs": upload.num_fovs,
        "disabled_fovs": upload.disabled_fovs,
        "channels": upload.channels,
        "settings_data": resolved_settings,
    }


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

    return serialize_upload(record, payload.settings_data)


@router.get(
    "/upload-step1/recent",
    response_model=list[schemas.Step1Out]
)
def recent_uploads(
    db: Session = Depends(get_db)
):
    uploads = (
        db.query(models.UploadStep1)
        .order_by(models.UploadStep1.id.desc())
        .limit(50)
        .all()
    )

    if not uploads:
        return []

    oldest_upload = uploads[-1]
    settings_records = (
        db.query(models.UploadSettings)
        .filter(models.UploadSettings.created_at >= oldest_upload.created_at)
        .order_by(models.UploadSettings.created_at.desc())
        .all()
    )

    result = []

    for index, upload in enumerate(uploads):
        newer_upload = uploads[index - 1] if index > 0 else None
        result.append(
            serialize_upload(
                upload,
                settings_for_upload(upload, newer_upload, settings_records)
            )
        )

    return result
