from datetime import datetime
from typing import Any

from pydantic import BaseModel

#------------------------------------------------
class Step1Create(BaseModel):
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


class Step1Out(Step1Create):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConfigCreate(Step1Create):
    config_name: str


class ConfigOut(ConfigCreate):
    id: int
    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True
#------------------------------------------------