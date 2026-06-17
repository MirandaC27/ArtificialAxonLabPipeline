from fastapi import APIRouter, Depends, HTTPException
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


@router.post("/configs", response_model=schemas.SavedConfigOut)
def save_config(config: schemas.SavedConfigCreate, db: Session = Depends(get_db)):
    result = config.a + config.b
    full_name = f"{config.first_name} {config.last_name}"

    max_order = db.query(models.SavedConfig).count()

    record = models.SavedConfig(
        config_name=config.config_name,
        a=config.a,
        b=config.b,
        result=result,
        first_name=config.first_name,
        last_name=config.last_name,
        full_name=full_name,
        order_index=max_order
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get("/configs", response_model=list[schemas.SavedConfigOut])
def get_configs(db: Session = Depends(get_db)):
    return (
        db.query(models.SavedConfig)
        .order_by(models.SavedConfig.order_index.asc())
        .all()
    )


@router.post("/configs/reorder")
def reorder_configs(config_ids: list[int], db: Session = Depends(get_db)):
    for index, config_id in enumerate(config_ids):
        config = db.query(models.SavedConfig).filter(
            models.SavedConfig.id == config_id
        ).first()

        if config:
            config.order_index = index

    db.commit()

    return {"status": "ok"}