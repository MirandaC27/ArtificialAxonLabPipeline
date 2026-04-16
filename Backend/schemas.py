from pydantic import BaseModel

class Numbers(BaseModel):
    a: int
    b: int

class Result(BaseModel):
    result: int