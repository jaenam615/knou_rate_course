# 방통대 꿀과목 DB

방송통신대학교(KNOU) 학생들을 위한 과목 평가 서비스입니다.
수강신청 시 **꿀과목**을 빠르게 찾을 수 있도록 후기와 평점 기반 검색을 제공합니다.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python 3.12+) |
| Database | PostgreSQL + SQLAlchemy (async) |
| Auth | JWT + bcrypt |
| API Docs | OpenAPI (Swagger UI / ReDoc) |

## Quick Start

### 1. Prerequisites

- Python 3.12+
- PostgreSQL (or Docker)
- [uv](https://github.com/astral-sh/uv) package manager

### 2. Setup

```bash
# Clone and enter directory
cd knou_rate_course

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Edit .env with your settings
```

### 3. Database Setup

**Option A: Docker**
```bash
docker run -d --name knou-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=knou_rate \
  -p 5432:5432 postgres:16
```

**Option B: Existing PostgreSQL**
```bash
createdb knou_rate
```

### 4. Seed Data

```bash
python -m app.db.seed
```

### 5. Run Server

```bash
uvicorn main:app --reload
```

### 6. Access API Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Clients                              │
│                  (Web / Mobile / etc.)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI App                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   API Layer (v1/)                    │   │
│  │  Controllers: auth, majors, courses, reviews, tags   │   │
│  │  - Request/Response handling                         │   │
│  │  - Input validation (Pydantic)                       │   │
│  │  - HTTP error responses                              │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                                │
│  ┌─────────────────────────▼───────────────────────────┐   │
│  │                  Service Layer                       │   │
│  │  - Business logic                                    │   │
│  │  - Domain rules (KNOU email validation)              │   │
│  │  - Cross-repository operations                       │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                                │
│  ┌─────────────────────────▼───────────────────────────┐   │
│  │                Repository Layer                      │   │
│  │  - Data access abstraction                           │   │
│  │  - SQLAlchemy queries                                │   │
│  │  - CRUD operations                                   │   │
│  └─────────────────────────┬───────────────────────────┘   │
└────────────────────────────┼────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      PostgreSQL                             │
│  Tables: users, majors, courses, course_offerings,          │
│          reviews, tags, review_tags                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
knou_rate_course/
├── main.py                      # FastAPI application entry point
├── pyproject.toml               # Dependencies (uv/pip)
├── .env                         # Environment variables
│
└── app/
    ├── config.py                # Settings (DB URL, JWT config)
    │
    ├── api/
    │   ├── __init__.py          # Router aggregation
    │   ├── deps.py              # Dependencies (JWT auth, get_current_user)
    │   └── v1/
    │       ├── auth.py          # POST /auth/signup, login, verify-email
    │       ├── majors.py        # GET /majors
    │       ├── courses.py       # GET /courses, GET /courses/{id}
    │       ├── reviews.py       # POST /courses/{id}/reviews
    │       └── tags.py          # GET /tags
    │
    ├── services/
    │   ├── auth.py              # Auth logic (signup, login, email validation)
    │   ├── course.py            # Course listing, detail with stats
    │   ├── major.py             # Major listing
    │   ├── review.py            # Review creation, duplicate check
    │   └── tag.py               # Tag listing
    │
    ├── repositories/
    │   ├── base.py              # Generic CRUD repository
    │   ├── user.py              # User queries
    │   ├── course.py            # Course queries with stats
    │   ├── major.py             # Major queries
    │   ├── review.py            # Review queries
    │   └── tag.py               # Tag queries
    │
    ├── models/
    │   ├── base.py              # SQLAlchemy declarative base
    │   ├── user.py              # User model
    │   ├── major.py             # Major model
    │   ├── course.py            # Course, CourseOffering models
    │   ├── review.py            # Review, ReviewTag models
    │   └── tag.py               # Tag model (EVAL_METHOD, FREEFORM)
    │
    ├── schemas/
    │   ├── auth.py              # SignupRequest, LoginRequest, TokenResponse
    │   ├── major.py             # MajorResponse
    │   ├── course.py            # CourseListResponse, CourseDetailResponse
    │   ├── review.py            # ReviewCreate, ReviewResponse
    │   └── tag.py               # TagResponse
    │
    └── db/
        ├── database.py          # Async session factory
        └── seed.py              # Initial data seeding
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/signup` | Register with KNOU email | - |
| POST | `/auth/verify-email` | Verify email with token | - |
| POST | `/auth/login` | Get JWT access token | - |
| POST | `/auth/resend-verification` | Resend verification email | - |
| GET | `/auth/me` | Get current user info | Required |

### Majors

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/majors` | List all majors | - |

### Courses

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/courses` | List courses with filters | - |
| GET | `/courses/{id}` | Course detail with reviews | - |

**Query Parameters for `GET /courses`:**
- `major_id` - Filter by major
- `q` - Search by course name
- `sort` - `top_rated` (default), `most_reviewed`, `latest`
- `limit` - Results per page (default: 20, max: 100)
- `offset` - Pagination offset

### Reviews

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/courses/{id}/reviews` | Create a review | Required |

**Request Body:**
```json
{
  "year": 2025,
  "semester": 1,
  "rating_overall": 5,
  "difficulty": 2,
  "workload": 3,
  "text": "좋은 강의였습니다...",
  "tag_ids": [1, 3, 5]
}
```

### Tags

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/tags` | List all tags | - |

---

## Data Model

```
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│   majors    │       │   courses   │       │ course_offerings│
├─────────────┤       ├─────────────┤       ├─────────────────┤
│ id          │◄──┐   │ id          │◄──┐   │ id              │
│ name        │   └───│ major_id    │   └───│ course_id       │
└─────────────┘       │ course_code │       │ year            │
                      │ name        │       │ semester        │
                      │ credits     │       │ grade_target    │
                      │ is_archived │       │ is_open         │
                      └─────────────┘       └─────────────────┘
                             │
                             │
┌─────────────┐       ┌──────▼──────┐       ┌─────────────┐
│    users    │       │   reviews   │       │    tags     │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │◄──┐   │ id          │───┐   │ id          │
│ email       │   └───│ user_id     │   │   │ name        │
│ password    │       │ course_id   │   │   │ type        │
│ is_verified │       │ year        │   │   └─────────────┘
│ verify_token│       │ semester    │   │          │
└─────────────┘       │ rating      │   │   ┌──────▼──────┐
                      │ difficulty  │   │   │ review_tags │
                      │ workload    │   │   ├─────────────┤
                      │ text        │   └───│ review_id   │
                      │ created_at  │       │ tag_id      │
                      │ is_hidden   │       └─────────────┘
                      └─────────────┘
```

### Tag Types

| Type | Examples | Description |
|------|----------|-------------|
| `EVAL_METHOD` | 기말시험, 기말과제물, 중간시험, 출석대체, 퀴즈, 팀플 | 고정 평가방식 태그 |
| `FREEFORM` | 기출많음, 오픈북, 암기위주, 이해위주, 과제헬, 점수잘줌 | 자유 태그 |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `DEBUG` | Enable debug mode (auto-create tables) | `false` |
| `JWT_SECRET_KEY` | Secret key for JWT signing | `change-me-in-production` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `10080` (7 days) |

---

## Authentication Flow

```
1. Signup
   POST /auth/signup { email: "student@knou.ac.kr", password: "..." }
   → 201 Created (verification email sent)

2. Verify Email
   POST /auth/verify-email { token: "..." }
   → 200 OK

3. Login
   POST /auth/login { email: "student@knou.ac.kr", password: "..." }
   → { access_token: "eyJ...", token_type: "bearer" }

4. Use Protected Endpoints
   POST /courses/1/reviews
   Headers: Authorization: Bearer eyJ...
```

**Note:** Only `@knou.ac.kr` email addresses are allowed.

---

## Development

### Run Tests
```bash
pytest
```

### Database Migrations (Alembic)
```bash
# Initialize (first time)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

---

## Deployment

### Recommended Stack
- **Frontend**: Vercel (Next.js)
- **Backend**: Render / Fly.io (FastAPI)
- **Database**: Supabase (PostgreSQL)

### Production Checklist
- [ ] Set secure `JWT_SECRET_KEY`
- [ ] Configure CORS origins properly
- [ ] Set `DEBUG=false`
- [ ] Enable HTTPS
- [ ] Set up email service for verification
- [ ] Configure rate limiting

---

## License

MIT
