from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .database import Base

#----------------------------------------------------------------
class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)

    a = Column(Integer)
    b = Column(Integer)
    result = Column(Integer)


#----------------------------------------------------------------
class Name(Base):
    __tablename__ = "names"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(200))


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