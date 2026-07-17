from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    JSON,
    String
)
from sqlalchemy.sql import func

from .database import Base


# ------------------------------------------------
# Combined workflow history
# ------------------------------------------------

class UploadStep1(Base):
    __tablename__ = "upload_step1"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    folders = Column(
        JSON,
        nullable=False,
        default=list
    )

    tracks = Column(
        JSON,
        nullable=False,
        default=list
    )

    tracks1 = Column(
        JSON,
        nullable=False,
        default=list
    )

    ordered_track = Column(
        JSON,
        nullable=False,
        default=list
    )

    data = Column(
        JSON,
        nullable=False,
        default=list
    )

    image_type = Column(
        String(20),
        nullable=False,
        default="3D"
    )

    microscope = Column(
        String(50),
        nullable=False,
        default="Keyence"
    )

    num_fovs = Column(
        Integer,
        nullable=False,
        default=0
    )

    disabled_fovs = Column(
        JSON,
        nullable=False,
        default=list
    )

    channels = Column(
        JSON,
        nullable=False,
        default=list
    )

    settings_data = Column(
        JSON,
        nullable=False,
        default=dict
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )


# ------------------------------------------------
# Optional separate settings history
# ------------------------------------------------

class UploadSettings(Base):
    __tablename__ = "upload_settings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    experiment = Column(
        String(100),
        nullable=False
    )

    frames = Column(
        Integer,
        nullable=False,
        default=0
    )

    distance = Column(
        String(100),
        nullable=False,
        default=""
    )

    run_ezra = Column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )


# ------------------------------------------------
# Saved configurations
# ------------------------------------------------

class UploadConfig(Base):
    __tablename__ = "upload_configs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    config_name = Column(
        String(100),
        nullable=False
    )

    folders = Column(
        JSON,
        nullable=False,
        default=list
    )

    tracks = Column(
        JSON,
        nullable=False,
        default=list
    )

    tracks1 = Column(
        JSON,
        nullable=False,
        default=list
    )

    ordered_track = Column(
        JSON,
        nullable=False,
        default=list
    )

    data = Column(
        JSON,
        nullable=False,
        default=list
    )

    image_type = Column(
        String(20),
        nullable=False,
        default="3D"
    )

    microscope = Column(
        String(50),
        nullable=False,
        default="Keyence"
    )

    num_fovs = Column(
        Integer,
        nullable=False,
        default=0
    )

    disabled_fovs = Column(
        JSON,
        nullable=False,
        default=list
    )

    channels = Column(
        JSON,
        nullable=False,
        default=list
    )

    settings_data = Column(
        JSON,
        nullable=False,
        default=dict
    )

    order_index = Column(
        Integer,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )