from datetime import datetime
from pydantic import BaseModel

# Add two numbers and return the result
class Numbers(BaseModel):
    a: int
    b: int

class Result(BaseModel):
    result: int


# First name and Last name and return the full name from different pages 
class NameInput(BaseModel):
    first_name: str
    last_name: str

class NameResult(BaseModel):
    full_name: str


# Combine all the inputs and results into a session
class SessionCreate(BaseModel):
    a: int
    b: int
    first_name: str
    last_name: str

#----------------------------------------------------------------
class SessionOut(BaseModel):
    id: int

    a: int
    b: int
    result: int

    first_name: str
    last_name: str
    full_name: str

    created_at: datetime

    class Config:
        from_attributes = True

#----------------------------------------------------------------
class SavedConfigCreate(BaseModel):
    config_name: str
    a: int
    b: int
    first_name: str
    last_name: str


class SavedConfigOut(BaseModel):
    id: int
    config_name: str

    a: int
    b: int
    result: int

    first_name: str
    last_name: str
    full_name: str

    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True

#----------------------------------------------------------------