from sqlalchemy import Column, Integer
from .database import Base

class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    a = Column(Integer)
    b = Column(Integer)
    result = Column(Integer)