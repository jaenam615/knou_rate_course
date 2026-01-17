from pydantic import BaseModel


class MajorResponse(BaseModel):
    id: int
    name: str
    department: str

    class Config:
        from_attributes = True
