from sqlalchemy import (Boolean, Column, DateTime, Integer, JSON, LargeBinary, String)
from sqlalchemy.sql import func

from .database import Base


# ------------------------------------------------
# Combined history

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

    masking_data = Column(JSON, nullable=False, default=dict)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )


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



class MaskingSettings(Base):
    __tablename__ = "masking_settings"

    id = Column(Integer, primary_key=True, index=True)
    base_path = Column(String, nullable=False, default="")
    well_start = Column(Integer, nullable=False, default=2)
    well_end = Column(Integer, nullable=False, default=11)
    thresholds = Column(JSON, nullable=False, default=dict)
    auto_thresholds = Column(JSON, nullable=False, default=dict)
    particle_size = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

# ------------------------------------------------
# Saved configurations

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

    masking_data = Column(JSON, nullable=False, default=dict)

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

class ResultCsv(Base):
    __tablename__ = "result_csvs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, unique=True, index=True)
    content = Column(LargeBinary, nullable=False)
    mime_type = Column(String(150), nullable=False, default="text/csv")
    artifact_type = Column(String(50), nullable=False, default="csv")
    job_id = Column(Integer, nullable=True, index=True)
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="queued", index=True)
    payload = Column(JSON, nullable=False, default=dict)
    result_id = Column(Integer, nullable=True)
    artifact_ids = Column(JSON, nullable=False, default=list)
    row_count = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
    progress = Column(Integer, nullable=False, default=0)
    progress_message = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
