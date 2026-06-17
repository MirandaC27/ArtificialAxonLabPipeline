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


@router.post("/sessions", response_model=schemas.SessionOut)
def save_session(
    session: schemas.SessionCreate,
    db: Session = Depends(get_db)
):
    result = session.a + session.b
    full_name = f"{session.first_name} {session.last_name}"

    record = models.SessionInput(
        a=session.a,
        b=session.b,
        result=result,
        first_name=session.first_name,
        last_name=session.last_name,
        full_name=full_name
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get("/sessions/recent")
def get_recent_sessions(
    db: Session = Depends(get_db)
):
    return (
        db.query(models.SessionInput)
        .order_by(models.SessionInput.id.desc())
        .limit(10)
        .all()
    )