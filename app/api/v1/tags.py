from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import TagResponse
from app.services import TagService
from app.utils import CurrentUser

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def get_tags(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[TagResponse]:
    service = TagService(db)
    tags = await service.get_all()
    return [TagResponse.model_validate(t) for t in tags]
