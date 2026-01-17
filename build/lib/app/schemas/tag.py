from pydantic import BaseModel

from app.models.tag import TagType


class TagResponse(BaseModel):
    id: int
    name: str
    type: TagType

    class Config:
        from_attributes = True
