from fastapi import APIRouter, Depends
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

@router.post("/name", response_model=schemas.NameResult)
def add_numbers(name: schemas.Name, db: Session = Depends(get_db)):
    result = f"{name.first_name} {name.last_name}"

    record = models.Name(
        first_name=name.first_name,
        last_name=name.last_name,
        result=result
    )

    db.add(record)
    db.commit()

    return {"result": result}
