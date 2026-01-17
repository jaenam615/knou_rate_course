"""
KNOU Course Scraper

Scrapes course data from KNOU (Korea National Open University) department websites.
Run with: python -m scripts.scrape_knou
"""

import asyncio
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# Department (college) to major mapping with curriculum URLs
DEPARTMENTS = {
    "인문과학대학": {
        "국어국문학과": "https://korean.knou.ac.kr/korean/5319/subview.do",
        "영어영문학과": "https://eng.knou.ac.kr/eng/5291/subview.do",
        "중어중문학과": "https://chl.knou.ac.kr/chl/5263/subview.do",
        "프랑스언어문화학과": "https://french.knou.ac.kr/french/5232/subview.do",
        "일본학과": "https://jpn.knou.ac.kr/jpn/5201/subview.do",
    },
    "사회과학대학": {
        "법학과": "https://law.knou.ac.kr/law/5170/subview.do",
        "행정학과": "https://pa.knou.ac.kr/pa/5140/subview.do",
        "경제학과": "https://econ.knou.ac.kr/econ/5113/subview.do",
        "경영학과": "https://biz.knou.ac.kr/biz/5086/subview.do",
        "무역학과": "https://trade.knou.ac.kr/trade/5057/subview.do",
        "미디어영상학과": "https://mas.knou.ac.kr/mas/5018/subview.do",
        "관광학과": "https://tourism.knou.ac.kr/tourism/4986/subview.do",
        "사회복지학과": "https://socialwelfare.knou.ac.kr/socialwelfare/4958/subview.do",
    },
    "자연과학대학": {
        "농학과": "https://agri.knou.ac.kr/agri/4901/subview.do",
        "생활과학부": "https://he.knou.ac.kr/he/4850/subview.do",
        "컴퓨터과학과": "https://cs.knou.ac.kr/cs1/4789/subview.do",
        "통계데이터과학과": "https://stat.knou.ac.kr/stat/4753/subview.do",
        "보건환경안전학과": "https://env.knou.ac.kr/env/4700/subview.do",
        "간호학과": "https://nursing.knou.ac.kr/nursing/6185/subview.do",
    },
    "교육과학대학": {
        "교육학과": "https://learn.knou.ac.kr/learn/4614/subview.do",
        "청소년교육과": "https://yedu.knou.ac.kr/yedu/4554/subview.do",
        "유아교육과": "https://ece.knou.ac.kr/ece/4508/subview.do",
        "문화교양학과": "https://bu45.knou.ac.kr/bu45/4475/subview.do",
        "생활체육지도과": "https://sports.knou.ac.kr/sports/6215/subview.do",
    },
}

# Flatten for easier iteration
DEPARTMENT_URLS = {}
MAJOR_TO_DEPARTMENT = {}
for dept, majors in DEPARTMENTS.items():
    for major, url in majors.items():
        DEPARTMENT_URLS[major] = url
        MAJOR_TO_DEPARTMENT[major] = dept


@dataclass
class Course:
    """Scraped course data."""

    course_code: str
    name: str
    major: str
    grade: int  # 1-4
    semester: int  # 1 or 2
    category: str = ""  # 전공, 교양, etc.


def parse_curriculum_table(html: str, major_name: str) -> list[Course]:
    """Parse curriculum table from HTML and extract courses."""
    soup = BeautifulSoup(html, "lxml")
    courses = []

    # Find tables - KNOU pages typically have curriculum in tables
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        current_grade = 0
        current_semester = 0

        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue

            # Extract text from cells
            cell_texts = [cell.get_text(strip=True) for cell in cells]

            # Try to find grade/semester info from row headers
            row_text = " ".join(cell_texts)

            # Check for grade-semester pattern like "1-1", "2-2", "1학년 1학기"
            grade_sem_match = re.search(
                r"(\d)[^\d]*[학년]?[^\d]*(\d)[^\d]*[학기]?", row_text
            )
            if grade_sem_match:
                try:
                    current_grade = int(grade_sem_match.group(1))
                    current_semester = int(grade_sem_match.group(2))
                    if current_grade > 4:
                        current_grade = 0
                    if current_semester > 2:
                        current_semester = 0
                except ValueError:
                    pass

            # Look for course code pattern (5-digit number)
            for i, text in enumerate(cell_texts):
                # Course codes are typically 5-digit numbers
                code_match = re.search(r"\b(\d{5})\b", text)
                if code_match:
                    course_code = code_match.group(1)

                    # Find course name - usually in adjacent cell or same cell
                    course_name = ""
                    category = ""

                    # Check adjacent cells for course name
                    for j, other_text in enumerate(cell_texts):
                        if j == i:
                            continue
                        # Course names are Korean text, not just numbers
                        if re.search(r"[가-힣]{2,}", other_text) and not re.search(
                            r"^\d+$", other_text
                        ):
                            # Skip category-like texts
                            if other_text in [
                                "전공",
                                "교양",
                                "일반선택",
                                "기초",
                                "심화",
                                "실습",
                            ]:
                                category = other_text
                            elif len(other_text) > 1 and len(other_text) < 50:
                                course_name = other_text
                                break

                    # If name not found in adjacent cells, try extracting from same cell
                    if not course_name:
                        name_match = re.search(
                            r"([가-힣A-Za-z0-9\s\+\-·]+)", text.replace(course_code, "")
                        )
                        if name_match:
                            course_name = name_match.group(1).strip()

                    if course_name and len(course_name) > 1:
                        # Determine grade/semester from position or context
                        grade = current_grade if current_grade > 0 else 1
                        semester = current_semester if current_semester > 0 else 1

                        course = Course(
                            course_code=course_code,
                            name=course_name,
                            major=major_name,
                            grade=grade,
                            semester=semester,
                            category=category,
                        )
                        courses.append(course)

    # Deduplicate by course code
    seen_codes = set()
    unique_courses = []
    for course in courses:
        if course.course_code not in seen_codes:
            seen_codes.add(course.course_code)
            unique_courses.append(course)

    return unique_courses


async def fetch_curriculum(
    client: httpx.AsyncClient, major: str, url: str
) -> list[Course]:
    """Fetch and parse curriculum for a department."""
    try:
        print(f"  Fetching {major}...")
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()

        courses = parse_curriculum_table(response.text, major)
        print(f"  Found {len(courses)} courses for {major}")
        return courses
    except httpx.HTTPError as e:
        print(f"  Error fetching {major}: {e}")
        return []
    except Exception as e:
        print(f"  Error parsing {major}: {e}")
        return []


async def scrape_all_departments() -> dict[str, list[Course]]:
    """Scrape courses from all departments."""
    all_courses: dict[str, list[Course]] = {}

    async with httpx.AsyncClient(
        timeout=30.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    ) as client:
        print("Starting KNOU course scraping...")
        print(f"Total departments: {len(DEPARTMENT_URLS)}")
        print("-" * 50)

        # Fetch in batches to avoid overwhelming the server
        batch_size = 5
        items = list(DEPARTMENT_URLS.items())

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            tasks = [fetch_curriculum(client, major, url) for major, url in batch]
            results = await asyncio.gather(*tasks)

            for (major, _), courses in zip(batch, results):
                all_courses[major] = courses

            # Small delay between batches
            if i + batch_size < len(items):
                await asyncio.sleep(1)

    return all_courses


def generate_seed_data(courses_by_major: dict[str, list[Course]]) -> dict:
    """Generate seed data structure from scraped courses."""
    # Build majors with department info
    majors = [
        {"name": name, "department": MAJOR_TO_DEPARTMENT.get(name, "기타")}
        for name in courses_by_major.keys()
    ]

    # Flatten courses with major reference
    all_courses = []
    for major, courses in courses_by_major.items():
        for course in courses:
            all_courses.append(asdict(course))

    return {
        "majors": majors,
        "courses": all_courses,
        "stats": {
            "total_majors": len(majors),
            "total_courses": len(all_courses),
            "courses_per_major": {
                major: len(courses) for major, courses in courses_by_major.items()
            },
        },
    }


async def main():
    """Main entry point."""
    # Scrape all departments
    courses_by_major = await scrape_all_departments()

    # Generate seed data
    seed_data = generate_seed_data(courses_by_major)

    # Print summary
    print("-" * 50)
    print("Scraping complete!")
    print(f"Total majors: {seed_data['stats']['total_majors']}")
    print(f"Total courses: {seed_data['stats']['total_courses']}")
    print("\nCourses per major:")
    for major, count in seed_data["stats"]["courses_per_major"].items():
        print(f"  {major}: {count}")

    # Save to JSON file
    output_path = Path(__file__).parent.parent / "data" / "knou_courses.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(seed_data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {output_path}")

    return seed_data


if __name__ == "__main__":
    asyncio.run(main())
