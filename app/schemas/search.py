from typing import Literal

from pydantic import BaseModel


class SearchResult(BaseModel):
    id: int
    course_code: str
    name: str
    major_name: str


class TrendingItem(BaseModel):
    rank: int
    name: str
    change: Literal["up", "down", "same", "new"]
    changeAmount: int
