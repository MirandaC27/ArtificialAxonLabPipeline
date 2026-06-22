from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base


#----------------------------------------------------------------
class SessionInput(Base):
    __tablename__ = "session_inputs"

    id = Column(Integer, primary_key=True, index=True)

    a = Column(Integer)
    b = Column(Integer)
    result = Column(Integer)

    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(200))

    created_at = Column(
        DateTime,
        server_default=func.now()
)   
    
#----------------------------------------------------------------
class SavedConfig(Base):
    __tablename__ = "saved_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_name = Column(String(100), nullable=False)

    a = Column(Integer)
    b = Column(Integer)
    result = Column(Integer)

    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(200))

    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

#----------------------------------------------------------------
class UploadStep1(Base):
    __tablename__ = "upload_step1"

    id = Column(Integer, primary_key=True, index=True)

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

    created_at = Column(DateTime(timezone=True), server_default=func.now())