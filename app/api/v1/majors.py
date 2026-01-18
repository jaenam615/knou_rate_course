from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps.cache import get_cache
from app.schemas import MajorResponse
from app.services import MajorService
from app.services.cache import RedisCache
from app.utils import CurrentUser

router = APIRouter()


@router.get("", response_model=list[MajorResponse])
async def get_majors(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
) -> list[dict]:
    service = MajorService(db=db, cache=cache)
    return await service.get_all()
