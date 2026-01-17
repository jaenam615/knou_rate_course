from pydantic import BaseModel


class MajorResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
