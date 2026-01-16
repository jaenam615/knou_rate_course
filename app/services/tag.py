from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tag
from app.repositories import TagRepository


class TagService:
    def __init__(self, db: AsyncSession):
        self.repo = TagRepository(db)

    async def get_all(self) -> list[Tag]:
        return await self.repo.get_all_ordered()
