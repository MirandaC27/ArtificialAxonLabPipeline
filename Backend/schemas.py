from typing import List, Optional
from pydantic import BaseModel, Field


class Numbers(BaseModel):
    a: int
    b: int


class NumberResult(BaseModel):
    result: int


class Name(BaseModel):
    first_name: str
    last_name: str


class NameResult(BaseModel):
    result: str


class ChannelItem(BaseModel):
    num: int
    label: str
    disabled: bool = False


class UploadedSettingsCreate(BaseModel):
    selected_folders: List[str] = Field(default_factory=list)
    image_type: str
    microscope: str
    num_fovs: int
    channels: List[ChannelItem] = Field(default_factory=list)
    disabled_fovs: List[str] = Field(default_factory=list)
    start_time: str


class EndTimeUpdate(BaseModel):
    end_time: str


class UploadedSettingsResult(BaseModel):
    id: int
    message: str
    selected_folders: List[str]
    image_type: str
    microscope: str
    num_fovs: int
    channels: List[dict]
    disabled_fovs: List[str]
    start_time: str
    end_time: Optional[str] = None

    class Config:
        from_attributes = True


