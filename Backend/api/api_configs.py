from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from ..database import SessionLocal
from .. import models
from .. import schemas


router = APIRouter(tags=["Configs"])


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.post(
    "/upload-configs",
    response_model=schemas.ConfigOut
)
def save_config(
    payload: schemas.ConfigCreate,
    db: Session = Depends(get_db)
):

    order_index = (
        db.query(models.UploadConfig)
        .count()
    )

    record = models.UploadConfig(
        **payload.model_dump(),
        order_index=order_index
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get(
    "/upload-configs",
    response_model=list[schemas.ConfigOut]
)
def get_configs(
    db: Session = Depends(get_db)
):

    return (
        db.query(models.UploadConfig)
        .order_by(models.UploadConfig.order_index)
        .all()
    )


@router.post(
    "/upload-configs/reorder"
)
def reorder(
    ids: list[int],
    db: Session = Depends(get_db)
):

    for index, config_id in enumerate(ids):

        config = (
            db.query(models.UploadConfig)
            .filter(
                models.UploadConfig.id == config_id
            )
            .first()
        )

        if config:
            config.order_index = index

    db.commit()

    return {"status": "ok"}