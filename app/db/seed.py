"""
Seed script for initial data.
Run with: python -m app.db.seed

To scrape fresh data first: python -m scripts.scrape_knou
"""

import asyncio
import json
import re
from pathlib import Path

from sqlalchemy import select

from app.constants.course_constants import CourseStatus
from app.db.database import AsyncSessionLocal, engine
from app.models import (
    Base,
    Major,
    Course,
    CourseOffering,
    Tag,
    TagType,
    User,
    Review,
    ReviewTag,
)


# Fixed tags (EVAL_METHOD)
EVAL_TAGS = [
    "기말시험",
    "기말과제물",
    "중간시험",
    "출석대체",
    "퀴즈",
    "팀플",
]

# Freeform tags
FREEFORM_TAGS = [
    "기출많음",
    "오픈북",
    "암기위주",
    "이해위주",
    "과제헬",
    "점수잘줌",
    "교수님친절",
    "강의재밌음",
]

# Department (college) mapping for majors
MAJOR_DEPARTMENTS = {
    # 인문과학대학 (College of Liberal Arts)
    "국어국문학과": "인문과학대학",
    "영어영문학과": "인문과학대학",
    "중어중문학과": "인문과학대학",
    "프랑스언어문화학과": "인문과학대학",
    "일본학과": "인문과학대학",
    # 사회과학대학 (College of Social Sciences)
    "법학과": "사회과학대학",
    "행정학과": "사회과학대학",
    "경제학과": "사회과학대학",
    "경영학과": "사회과학대학",
    "무역학과": "사회과학대학",
    "미디어영상학과": "사회과학대학",
    "관광학과": "사회과학대학",
    "사회복지학과": "사회과학대학",
    # 자연과학대학 (College of Natural Sciences)
    "농학과": "자연과학대학",
    "생활과학부": "자연과학대학",
    "컴퓨터과학과": "자연과학대학",
    "통계데이터과학과": "자연과학대학",
    "보건환경안전학과": "자연과학대학",
    "간호학과": "자연과학대학",
    # 교육과학대학 (College of Education)
    "교육학과": "교육과학대학",
    "청소년교육과": "교육과학대학",
    "유아교육과": "교육과학대학",
    "문화교양학과": "교육과학대학",
    "생활체육지도과": "교육과학대학",
}


def slugify(name: str) -> str:
    """Convert Korean major name to URL-friendly slug."""
    # Simple mapping for common names
    slug_map = {
        "국어국문학과": "korean",
        "영어영문학과": "english",
        "중어중문학과": "chinese",
        "프랑스언어문화학과": "french",
        "일본학과": "japanese",
        "법학과": "law",
        "행정학과": "public-admin",
        "경제학과": "economics",
        "경영학과": "business",
        "무역학과": "trade",
        "미디어영상학과": "media",
        "관광학과": "tourism",
        "사회복지학과": "social-welfare",
        "농학과": "agriculture",
        "생활과학부": "life-science",
        "컴퓨터과학과": "computer-science",
        "통계데이터과학과": "statistics",
        "보건환경안전학과": "health-environment",
        "간호학과": "nursing",
        "교육학과": "education",
        "청소년교육과": "youth-education",
        "유아교육과": "early-childhood",
        "문화교양학과": "liberal-arts",
        "생활체육지도과": "sports",
    }
    return slug_map.get(name, re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"))


def load_scraped_data() -> dict:
    """Load scraped course data from JSON file."""
    data_path = Path(__file__).parent.parent.parent / "data" / "knou_courses.json"

    if not data_path.exists():
        print(f"Warning: Scraped data not found at {data_path}")
        print("Run 'python -m scripts.scrape_knou' to scrape data first.")
        return {"majors": [], "courses": []}

    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def seed_database():
    """Seed the database with scraped KNOU data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Major))
        if result.first():
            print("Database already seeded. Skipping...")
            return

        # Load scraped data
        data = load_scraped_data()
        majors_list = data.get("majors", [])
        courses_list = data.get("courses", [])

        if not majors_list:
            print("No majors found in scraped data.")
            return

        # Seed majors with new fields
        majors = {}
        for major_data in majors_list:
            # Handle both old format (string) and new format (dict)
            if isinstance(major_data, str):
                name = major_data
                department = MAJOR_DEPARTMENTS.get(name, "기타")
            else:
                name = major_data["name"]
                department = major_data.get("department", MAJOR_DEPARTMENTS.get(name, "기타"))

            major = Major(
                name=name,
                department=department,
                slug=slugify(name),
                is_active=True,
            )
            db.add(major)
            majors[name] = major
        await db.flush()
        print(f"Added {len(majors_list)} majors")

        # Seed tags
        tags = {}
        for name in EVAL_TAGS:
            tag = Tag(name=name, type=TagType.EVAL_METHOD)
            db.add(tag)
            tags[name] = tag
        for name in FREEFORM_TAGS:
            tag = Tag(name=name, type=TagType.FREEFORM)
            db.add(tag)
            tags[name] = tag
        await db.flush()
        print(f"Added {len(EVAL_TAGS) + len(FREEFORM_TAGS)} tags")

        # Seed courses from scraped data
        course_count = 0
        offering_count = 0
        seen_course_codes = set()

        for course_data in courses_list:
            course_code = course_data["course_code"]
            major_name = course_data["major"]

            # Skip duplicates (same course may appear in multiple majors as 교양)
            if course_code in seen_course_codes:
                continue
            seen_course_codes.add(course_code)

            # Skip if major not found (e.g., courses from departments with 0 results)
            if major_name not in majors:
                continue

            major = majors[major_name]

            course = Course(
                major_id=major.id,
                course_code=course_code,
                name=course_data["name"],
                credits=course_data.get("credits", 3),
            )
            db.add(course)
            course_count += 1

            # Create course offering with new schema
            await db.flush()  # Need course.id
            offering = CourseOffering(
                course_id=course.id,
                semester=course_data.get("semester", 1),
                grade_target=course_data.get("grade", 1),
                status=CourseStatus.ACTIVE,
            )
            db.add(offering)
            offering_count += 1

        await db.flush()
        print(f"Added {course_count} courses")
        print(f"Added {offering_count} course offerings")

        # Create a test user for sample reviews
        test_user = User(
            email="test@knou.ac.kr",
            password_hash="$2b$12$test_hash_not_for_login",  # Not a real password
            is_verified=True,
        )
        db.add(test_user)
        await db.flush()

        # Add sample reviews for demonstration
        cs_courses_result = await db.execute(
            select(Course).join(Major).where(Major.name == "컴퓨터과학과").limit(3)
        )
        cs_courses = cs_courses_result.scalars().all()

        if cs_courses:
            sample_texts = [
                "좋은 강의입니다. 기초부터 차근차근 설명해주셔서 이해하기 쉬웠어요. 과제도 적당하고 시험도 기출 위주라 공부하기 좋았습니다.",
                "프로그래밍 실습 위주라 실력이 많이 늘었습니다. 처음에는 어려웠지만 꾸준히 하니까 따라갈 수 있었어요.",
                "온라인 강의 자료가 잘 되어있어요. 반복해서 볼 수 있어서 좋고, 교수님 설명도 친절합니다.",
            ]
            sample_reviews = []
            for i, course in enumerate(cs_courses):
                review = Review(
                    course_id=course.id,
                    user_id=test_user.id,
                    rating_overall=4 + (i % 2),
                    difficulty=2 + (i % 3),
                    workload=2 + (i % 3),
                    text=sample_texts[i],
                )
                db.add(review)
                sample_reviews.append(review)

            await db.flush()

            # Add tags to first sample review
            tag_기출많음 = tags["기출많음"]
            tag_점수잘줌 = tags["점수잘줌"]
            tag_기말시험 = tags["기말시험"]

            if sample_reviews:
                db.add(
                    ReviewTag(review_id=sample_reviews[0].id, tag_id=tag_기출많음.id)
                )
                db.add(
                    ReviewTag(review_id=sample_reviews[0].id, tag_id=tag_점수잘줌.id)
                )
                db.add(
                    ReviewTag(review_id=sample_reviews[0].id, tag_id=tag_기말시험.id)
                )

            print(f"Added {len(sample_reviews)} sample reviews with tags")

        await db.commit()
        print("Seeding complete!")


async def clear_database():
    """Clear all data from the database (for development)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database cleared and recreated.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_database())
    else:
        asyncio.run(seed_database())
