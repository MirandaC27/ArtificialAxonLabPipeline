from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import SessionLocal
from . import models, schemas

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

'''
Tkinter → POST → Postgres  
                 ↓
        GET export → JSON  
'''        

@router.post("/upload_settings", response_model=schemas.UploadedSettingsResult)
def upload_settings(
    settings: schemas.UploadedSettingsCreate,
    db: Session = Depends(get_db),
):
    record = models.UploadedSettings(
        selected_folders=settings.selected_folders,
        image_type=settings.image_type,
        microscope=settings.microscope,
        num_fovs=settings.num_fovs,
        channels=[channel.model_dump() for channel in settings.channels],
        disabled_fovs=settings.disabled_fovs,
        start_time=settings.start_time,
        end_time=None,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "message": "Settings saved to Postgres",
        "selected_folders": record.selected_folders,
        "image_type": record.image_type,
        "microscope": record.microscope,
        "num_fovs": record.num_fovs,
        "channels": record.channels,
        "disabled_fovs": record.disabled_fovs,
        "start_time": record.start_time,
        "end_time": record.end_time,
    }


@router.patch("/upload_settings/latest/end_time")
def update_latest_end_time(
    payload: schemas.EndTimeUpdate,
    db: Session = Depends(get_db),
):
    record = (
        db.query(models.UploadedSettings)
        .order_by(models.UploadedSettings.id.desc())
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="No settings found")

    record.end_time = payload.end_time
    db.commit()
    db.refresh(record)

    return {
        "message": "End time updated",
        "id": record.id,
        "end_time": record.end_time,
    }


@router.get("/export_settings/latest")
def export_latest_settings(db: Session = Depends(get_db)):
    record = (
        db.query(models.UploadedSettings)
        .order_by(models.UploadedSettings.id.desc())
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="No settings found")

    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    file_path = data_dir / "upload_settings.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"Session ID: {record.id}\n")
        f.write(f"Start Time: {record.start_time}\n")
        f.write(f"End Time: {record.end_time or 'N/A'}\n")
        f.write(f"Microscope: {record.microscope}\n")
        f.write(f"Image Type: {record.image_type}\n")
        f.write(f"Number of FOVs: {record.num_fovs}\n")

        f.write("\nSelected Folders:\n")
        for folder in record.selected_folders or []:
            f.write(f"- {folder}\n")

        f.write("\nChannels:\n")
        for ch in record.channels or []:
            status = "Disabled" if ch.get("disabled") else "Active"
            f.write(
                f"- Channel {ch.get('num')}: {ch.get('label')} ({status})\n"
            )

        f.write("\nDisabled FOVs:\n")
        for fov in record.disabled_fovs or []:
            f.write(f"- {fov}\n")

    return {
        "message": "Latest settings exported to text file",
        "file": str(file_path),
        "id": record.id,
    }