from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Major
from app.repositories.base import BaseRepository


class MajorRepository(BaseRepository[Major]):
    def __init__(self, db: AsyncSession):
        super().__init__(Major, db)

    async def get_all_ordered(self) -> list[Major]:
        result = await self.db.execute(select(Major).order_by(Major.name))
        return list(result.scalars().all())
