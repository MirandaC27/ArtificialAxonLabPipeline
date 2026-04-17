from sqlalchemy import Column, Integer, String
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