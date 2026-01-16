from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    def __init__(self, db: AsyncSession):
        super().__init__(Tag, db)

    async def get_all_ordered(self) -> list[Tag]:
        result = await self.db.execute(select(Tag).order_by(Tag.type, Tag.name))
        return list(result.scalars().all())

    async def get_by_ids(self, tag_ids: list[int]) -> list[Tag]:
        if not tag_ids:
            return []
        result = await self.db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        return list(result.scalars().all())
