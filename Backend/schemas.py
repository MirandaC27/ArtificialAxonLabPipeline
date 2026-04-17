from pydantic import BaseModel

class Numbers(BaseModel):
    a: int
    b: int

class NumberResult(BaseModel):
    result: int

class Name(BaseModel):
    first_name: str
    last_name: str

class NameResult(BaseModel):
    result: str