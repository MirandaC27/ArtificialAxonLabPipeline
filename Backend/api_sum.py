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

@router.post("/add", response_model=schemas.Result)
def add_numbers(nums: schemas.Numbers, db: Session = Depends(get_db)):
    result = nums.a + nums.b

    record = models.Calculation(
        a=nums.a,
        b=nums.b,
        result=result
    )

    db.add(record)
    db.commit()

    return {"result": result}