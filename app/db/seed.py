"""
Seed script for initial data.
Run with: python -m app.db.seed
"""

import asyncio

from sqlalchemy import select

from app.db.database import AsyncSessionLocal, engine
from app.models import Base, Major, Course, Tag, TagType, Review, ReviewTag


# Sample majors (KNOU departments)
MAJORS = [
    "국어국문학과",
    "영어영문학과",
    "중어중문학과",
    "프랑스언어문화학과",
    "일본학과",
    "법학과",
    "행정학과",
    "경제학과",
    "경영학과",
    "무역학과",
    "미디어영상학과",
    "관광학과",
    "농학과",
    "가정학과",
    "컴퓨터과학과",
    "정보통계학과",
    "환경보건학과",
    "간호학과",
    "유아교육과",
    "문화교양학과",
    "청소년교육과",
    "생활체육지도학과",
]

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

# Sample courses for 컴퓨터과학과
CS_COURSES = [
    ("CS101", "컴퓨터과학개론", 3),
    ("CS102", "이산수학", 3),
    ("CS201", "자료구조", 3),
    ("CS202", "알고리즘", 3),
    ("CS203", "컴퓨터구조", 3),
    ("CS204", "운영체제", 3),
    ("CS301", "데이터베이스", 3),
    ("CS302", "컴퓨터네트워크", 3),
    ("CS303", "소프트웨어공학", 3),
    ("CS304", "프로그래밍언어론", 3),
    ("CS401", "인공지능", 3),
    ("CS402", "머신러닝", 3),
]

# Sample courses for 경영학과
BIZ_COURSES = [
    ("BIZ101", "경영학원론", 3),
    ("BIZ102", "회계원리", 3),
    ("BIZ201", "마케팅원론", 3),
    ("BIZ202", "재무관리", 3),
    ("BIZ203", "인적자원관리", 3),
    ("BIZ301", "경영전략", 3),
    ("BIZ302", "소비자행동론", 3),
]

# Sample courses for 행정학과
PA_COURSES = [
    ("PA101", "행정학개론", 3),
    ("PA102", "정책학개론", 3),
    ("PA201", "조직론", 3),
    ("PA202", "인사행정론", 3),
    ("PA301", "지방자치론", 3),
]


async def seed_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Major))
        if result.first():
            print("Database already seeded. Skipping...")
            return

        # Seed majors
        majors = {}
        for name in MAJORS:
            major = Major(name=name)
            db.add(major)
            majors[name] = major
        await db.flush()
        print(f"Added {len(MAJORS)} majors")

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

        # Seed courses
        cs_major = majors["컴퓨터과학과"]
        for code, name, credits in CS_COURSES:
            course = Course(
                major_id=cs_major.id,
                course_code=code,
                name=name,
                credits=credits,
            )
            db.add(course)

        biz_major = majors["경영학과"]
        for code, name, credits in BIZ_COURSES:
            course = Course(
                major_id=biz_major.id,
                course_code=code,
                name=name,
                credits=credits,
            )
            db.add(course)

        pa_major = majors["행정학과"]
        for code, name, credits in PA_COURSES:
            course = Course(
                major_id=pa_major.id,
                course_code=code,
                name=name,
                credits=credits,
            )
            db.add(course)

        await db.flush()
        print(f"Added {len(CS_COURSES) + len(BIZ_COURSES) + len(PA_COURSES)} courses")

        # Add sample reviews
        cs_intro_result = await db.execute(
            select(Course).where(Course.course_code == "CS101")
        )
        cs_intro = cs_intro_result.scalar_one()

        sample_reviews = [
            Review(
                course_id=cs_intro.id,
                year=2024,
                semester=1,
                rating_overall=5,
                difficulty=2,
                workload=2,
                text="컴퓨터과학 입문으로 최고! 기초부터 차근차근 설명해주셔서 비전공자도 이해하기 쉬웠어요. 과제도 적당하고 시험도 기출 위주라 공부하기 좋았습니다.",
            ),
            Review(
                course_id=cs_intro.id,
                year=2024,
                semester=2,
                rating_overall=4,
                difficulty=3,
                workload=3,
                text="전반적으로 괜찮은 과목입니다. 프로그래밍 기초가 없으면 좀 어려울 수 있어요. 그래도 강의 자료가 잘 되어있어서 독학 가능합니다.",
            ),
            Review(
                course_id=cs_intro.id,
                year=2025,
                semester=1,
                rating_overall=5,
                difficulty=2,
                workload=2,
                text="꿀과목 인정! 교수님 설명도 좋고 시험도 어렵지 않아요. 컴과 입문으로 강추합니다.",
            ),
        ]

        for review in sample_reviews:
            db.add(review)
        await db.flush()

        # Add tags to reviews
        tag_기출많음 = tags["기출많음"]
        tag_점수잘줌 = tags["점수잘줌"]
        tag_기말시험 = tags["기말시험"]

        db.add(ReviewTag(review_id=sample_reviews[0].id, tag_id=tag_기출많음.id))
        db.add(ReviewTag(review_id=sample_reviews[0].id, tag_id=tag_점수잘줌.id))
        db.add(ReviewTag(review_id=sample_reviews[0].id, tag_id=tag_기말시험.id))
        db.add(ReviewTag(review_id=sample_reviews[2].id, tag_id=tag_기출많음.id))
        db.add(ReviewTag(review_id=sample_reviews[2].id, tag_id=tag_기말시험.id))

        await db.commit()
        print("Added sample reviews with tags")
        print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
