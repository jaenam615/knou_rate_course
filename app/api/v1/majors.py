from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas import MajorResponse
from app.services import MajorService
from app.utils import CurrentUser

router = APIRouter()


@router.get("", response_model=list[MajorResponse])
async def get_majors(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[MajorResponse]:
    service = MajorService(db)
    majors = await service.get_all()
    return [MajorResponse.model_validate(m) for m in majors]
