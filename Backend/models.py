from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base


#----------------------------------------------------------------
class UploadStep1(Base):
    __tablename__ = "upload_step1"

    id = Column(Integer, primary_key=True)

    folders = Column(JSON)
    tracks = Column(JSON)
    tracks1 = Column(JSON)
    ordered_track = Column(JSON)
    data = Column(JSON)

    image_type = Column(String(20))
    microscope = Column(String(50))
    num_fovs = Column(Integer)

    disabled_fovs = Column(JSON)
    channels = Column(JSON)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class UploadConfig(Base):
    __tablename__ = "upload_configs"

    id = Column(Integer, primary_key=True)

    config_name = Column(String(100))

    folders = Column(JSON)
    tracks = Column(JSON)
    tracks1 = Column(JSON)
    ordered_track = Column(JSON)
    data = Column(JSON)

    image_type = Column(String(20))
    microscope = Column(String(50))
    num_fovs = Column(Integer)

    disabled_fovs = Column(JSON)
    channels = Column(JSON)

    order_index = Column(Integer, default=0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )