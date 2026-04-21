from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base

class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    a = Column(Integer)
    b = Column(Integer)
    result = Column(Integer)

class Name(Base):
    __tablename__ = "names"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    result = Column(String)

class UploadedSettings(Base):
    __tablename__ = "uploaded_settings"

    id = Column(Integer, primary_key=True, index=True)
    selected_folders = Column(JSONB, nullable=False, default=list)
    image_type = Column(String, nullable=False)
    microscope = Column(String, nullable=False)
    num_fovs = Column(Integer, nullable=False)
    channels = Column(JSONB, nullable=False, default=list)
    disabled_fovs = Column(JSONB, nullable=False, default=list)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=True)