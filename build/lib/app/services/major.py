from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Major
from app.repositories import MajorRepository


class MajorService:
    def __init__(self, db: AsyncSession):
        self.repo = MajorRepository(db)

    async def get_all(self) -> list[Major]:
        return await self.repo.get_all_ordered()
