from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.courses import router as courses_router
from app.api.v1.majors import router as majors_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.search import router as search_router
from app.api.v1.tags import router as tags_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(majors_router, prefix="/majors", tags=["majors"])
api_router.include_router(courses_router, prefix="/courses", tags=["courses"])
api_router.include_router(reviews_router, tags=["reviews"])
api_router.include_router(tags_router, prefix="/tags", tags=["tags"])
api_router.include_router(search_router, tags=["search"])
