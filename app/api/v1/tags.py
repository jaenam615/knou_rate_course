from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import TagResponse
from app.services import TagService

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def get_tags(db: AsyncSession = Depends(get_db)) -> list[TagResponse]:
    service = TagService(db)
    tags = await service.get_all()
    return [TagResponse.model_validate(t) for t in tags]
