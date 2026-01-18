import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api import api_router
from app.config import settings
from app.core.middleware import SecurityHeadersMiddleware
from app.core.rate_limit import limiter
from app.db import engine
from app.db.redis import get_redis, close_redis
from app.models import Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.debug:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup
    await close_redis()


app = FastAPI(
    title="방통대 꿀과목 DB",
    description="""
## 방송통신대학교 과목 평가 서비스 API

KNOU 학생들이 수강신청 시 **꿀과목**을 빠르게 찾을 수 있도록 돕는 서비스입니다.

### 주요 기능
- **전공별 과목 탐색**: 전공/학년/학기 기준으로 과목 검색
- **후기 및 평점**: 평점, 난이도, 과제량 기반 과목 평가
- **태그 시스템**: 기말시험/기말과제물/기출많음 등 태그로 필터링

### 인증
- KNOU 이메일(`@knou.ac.kr`)로만 가입 가능
- 이메일 인증 후 JWT 토큰 발급
- 후기 작성 시 인증 필요
    """,
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "auth",
            "description": "인증 관련 API (회원가입, 로그인, 이메일 인증)",
        },
        {"name": "majors", "description": "전공 목록 조회"},
        {"name": "courses", "description": "과목 조회 및 검색"},
        {"name": "reviews", "description": "후기 작성 (인증 필요)"},
        {"name": "tags", "description": "태그 목록 조회"},
    ],
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware, debug=settings.debug)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint that verifies database and Redis connectivity.
    Returns 200 if all services are healthy, 503 if any service is down.
    """
    health = {
        "status": "ok",
        "services": {
            "database": "ok",
            "redis": "ok",
        },
    }

    # Check database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        health["status"] = "degraded"
        health["services"]["database"] = "error"

    # Check Redis connection
    try:
        redis_client = await get_redis()
        await redis_client.ping()
    except Exception as e:
        logger.error("Redis health check failed: %s", e)
        health["status"] = "degraded"
        health["services"]["redis"] = "error"

    if health["status"] != "ok":
        from fastapi.responses import JSONResponse

        return JSONResponse(content=health, status_code=503)

    return health
