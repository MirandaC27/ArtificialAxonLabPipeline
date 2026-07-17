from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Step1Create(BaseModel):
    folders: list = []
    tracks: list = []
    tracks1: list = []
    ordered_track: list = []
    data: list = []

    image_type: str = "3D"
    microscope: str = "Keyence"
    num_fovs: int = 0

    disabled_fovs: list = []
    channels: list = []

    settings_data: dict = {}


class Step1Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    folders: list = []
    tracks: list = []
    tracks1: list = []
    ordered_track: list = []
    data: list = []
    image_type: str = "3D"
    microscope: str = "Keyence"
    num_fovs: int = 0
    disabled_fovs: list = []
    channels: list = []
    settings_data: dict = {}
    created_at: datetime | None = None


class SettingsCreate(BaseModel):
    experiment: str
    frames: int = 0
    distance: str = ""
    run_ezra: bool = False


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment: str
    frames: int = 0
    distance: str = ""
    run_ezra: bool = False
    created_at: datetime | None = None


class ConfigCreate(BaseModel):
    config_name: str
    folders: list = []
    tracks: list = []
    tracks1: list = []
    ordered_track: list = []
    data: list = []
    image_type: str = "3D"
    microscope: str = "Keyence"
    num_fovs: int = 0
    disabled_fovs: list = []
    channels: list = []
    settings_data: dict = {}


class ConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    config_name: str
    folders: list = []
    tracks: list = []
    tracks1: list = []
    ordered_track: list = []
    data: list = []
    image_type: str = "3D"
    microscope: str = "Keyence"
    num_fovs: int = 0
    disabled_fovs: list = []
    channels: list = []
    settings_data: dict = {}
    order_index: int = 0
    created_at: datetime | None = None
