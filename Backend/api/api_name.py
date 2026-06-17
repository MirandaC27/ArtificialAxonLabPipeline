from fastapi import APIRouter

from .. import schemas

router = APIRouter()

@router.post("/name", response_model=schemas.NameResult)
def combine_name(name: schemas.NameInput):
    full_name = f"{name.first_name} {name.last_name}"
    return {"full_name": full_name}
