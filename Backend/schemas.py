from datetime import datetime
from pydantic import BaseModel

# Combine all the inputs and results into a session
class SessionCreate(BaseModel):
    a: int
    b: int
    first_name: str
    last_name: str

#----------------------------------------------------------------
class SessionOut(BaseModel):
    id: int

    a: int
    b: int
    result: int

    first_name: str
    last_name: str
    full_name: str

    created_at: datetime

    class Config:
        from_attributes = True

#----------------------------------------------------------------
class SavedConfigCreate(BaseModel):
    config_name: str
    a: int
    b: int
    first_name: str
    last_name: str


class SavedConfigOut(BaseModel):
    id: int
    config_name: str

    a: int
    b: int
    result: int

    first_name: str
    last_name: str
    full_name: str

    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True

#----------------------------------------------------------------
from pydantic import BaseModel
from datetime import datetime
from typing import Any


class UploadStep1Create(BaseModel):
    folders: list[str]
    tracks: list[str]
    tracks1: list[str]
    ordered_track: list[str]
    data: list[str]

    image_type: str
    microscope: str
    num_fovs: int

    disabled_fovs: list[str]
    channels: list[dict[str, Any]]


class UploadStep1Out(UploadStep1Create):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True