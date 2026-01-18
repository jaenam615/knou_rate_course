from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import MajorRepository
from app.schemas import MajorResponse
from app.services.cache import RedisCache


class MajorService:
    def __init__(self, db: AsyncSession, cache: RedisCache):
        self.repo = MajorRepository(db)
        self.cache = cache

    async def get_all(self) -> list[dict]:
        return await self.cache.get_or_set_json(
            key="majors:all:v1",
            ttl=3600,
            loader=self._load_majors,
        )

    async def _load_majors(self) -> list[dict]:
        majors = await self.repo.get_all_ordered()
        return [MajorResponse.model_validate(m).model_dump() for m in majors]
