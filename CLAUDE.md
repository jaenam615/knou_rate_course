# CLAUDE.md — 방통대 꿀과목 DB (MVP)

## 0) 프로젝트 목적
방송통신대학교(방통대) 학생들이 수강신청/수강계획을 세울 때, DC인사이드나 카톡방 검색 없이 **전공/학년/학기 기준으로 과목을 탐색**하고 **후기/평점 기반으로 꿀과목을 빠르게 찾을 수 있는 웹 서비스**를 만든다.

MVP 목표는 “2주 내 출시”이며, 기능을 최소화하고 **검색/내비게이션/리스트 UX**에 집중한다.

---

## 1) 핵심 요구사항 (MVP 범위)

### 필수 기능 (반드시 포함)
1. **전공(Major) 목록 조회**
2. **전공별 과목(Course) 목록 조회**
   - 필터: 학년(grade), 학기(year/semester), 태그(tag)
   - 정렬: 평점순, 후기수순, 최신후기순
3. **과목 상세 페이지**
   - 과목 메타데이터
   - 후기 목록
   - 태그 요약
4. **후기 작성**
   - 평점(1~5)
   - 난이도(1~5)
   - 과제량(1~5)
   - 후기 텍스트
   - 학기(year/semester)
   - 태그 선택(기말시험/기말과제물 등)

### 선택 기능 (시간 남으면)
- “도움돼요” 투표
- 전공별/학기별 “꿀과목 TOP” 랭킹

### MVP에서 제외 (절대 넣지 않기)
- OCR/AI 성적 인증
- WebSocket/실시간 기능
- 복잡한 추천 알고리즘
- 관리자 UI를 예쁘게 만들기 (최소한의 운영 기능만)

---

## 2) 정보 구조(IA) / 내비게이션
서비스는 두 가지 진입 흐름을 제공한다.

### 탐색형
전공 선택 → 학년/학기 필터 → 과목 리스트 → 과목 상세 → 후기 확인

### 검색형
상단 검색(과목명/키워드) + 필터(전공/학년/학기/태그) → 과목 리스트 → 상세

> UI는 전공 > 학년 > 학기 > 과목처럼 보이게 할 수 있으나, DB는 계층으로 고정하지 않고 Offering 기반 필터로 구현한다.

---

## 3) 데이터 모델 (DB 설계 원칙)
- `Course`는 “과목 정체성”으로 **삭제하지 않고 영구 보존**한다.
- 학년/학기 분류는 태그가 아니라 **정규 필드**로 관리한다.
- 과목이 미개설/폐지되어도 과목 및 후기 데이터는 남아야 한다. (soft delete/archived)

### 엔티티
- **majors**
  - id, name
- **courses**
  - id, major_id, course_code, name, credits, is_archived
- **course_offerings**
  - id, course_id, year, semester, grade_target, is_open
- **reviews**
  - id, course_id, year, semester
  - rating_overall(1~5), difficulty(1~5), workload(1~5)
  - text, created_at, is_hidden
- **tags**
  - id, name, type
  - type: `EVAL_METHOD`(고정), `FREEFORM`(자유)
- **review_tags**
  - review_id, tag_id
- (옵션) **course_tags**
  - course_id, tag_id

### 고정 태그 예시 (EVAL_METHOD)
- 기말시험
- 기말과제물
- 중간시험
- 출석대체
- 퀴즈
- 팀플

### 자유 태그 예시 (FREEFORM)
- 기출많음
- 오픈북
- 암기위주
- 이해위주
- 과제헬
- 점수잘줌

---

## 4) Postgres를 선택하는 이유 (MySQL 대신)
이 서비스는 CRUD보다 **검색/필터/랭킹**이 핵심이며, Postgres가 특히 유리하다.

- 후기 텍스트 기반 검색을 DB에서 처리하기 쉬움 (`tsvector` Full Text Search)
- 과목명/키워드 부분검색 및 유사 검색에 유리 (`pg_trgm`)
- 전공/학년/학기/태그 조합 필터 + 집계(평점 평균, 후기수) 쿼리 작성이 편함
- 관리형 서비스(Supabase 등)로 빠른 런칭에 적합

---

## 5) 트래픽/운영 가정
- 평시 트래픽: 낮음
- 수강신청 기간: burst 트래픽 (읽기 폭증)
- read/write 비율: 평시 read-heavy, 시즌에는 write 증가(후기 작성)

---

## 6) 비기능 요구사항 (NFR)
### 성능
- 리스트/검색 P95 < 1s
- 상세 P95 < 500ms
- 페이지네이션 필수 (무제한 리스트 금지)

### 확장성 (시즌 트래픽 대응)
- API 서버는 stateless
- 핫 엔드포인트는 캐시 적용 가능해야 함
  - 전공별 과목 리스트
  - 랭킹/Top N

### 비용
- 비수기 비용 최소화 (scale-to-zero 또는 최소 인스턴스)
- 초기에는 Redis 없이도 운영 가능, 시즌 전에 추가 고려

### 신뢰도/안전
- 악성/도배 방지: rate limiting
- 동일 과목에 대해 학기당 1개의 후기만 허용(선택)
- 신고/블라인드(soft hide) 기능
- 개인정보(전화번호/카톡ID/링크) 포함 텍스트 제한(선택)

---

## 7) 권장 아키텍처 (MVP)
- Frontend: **Next.js**
- Backend: **FastAPI**
- DB: **Postgres (Supabase 추천)**
- Deploy: Vercel(프론트) + Render/Fly.io(백엔드) + Supabase(DB)

초기에는 단일 모놀리식 API로 운영한다.
마이그레이션을 고려하여 API 계약과 DB 스키마를 안정적으로 유지한다.

---

## 8) API (MVP 엔드포인트 초안)
### Major
- `GET /majors`

### Courses
- `GET /courses`
  - query: `major_id`, `year`, `semester`, `grade`, `tags`, `q`, `sort`
- `GET /courses/{course_id}`

### Reviews
- `GET /courses/{course_id}/reviews`
  - query: `year`, `semester`, `sort`
- `POST /courses/{course_id}/reviews`
  - body: rating_overall, difficulty, workload, text, year, semester, tags[]

(선택)
- `POST /reviews/{review_id}/vote` (도움돼요)

---

## 9) 검색/필터 규칙 (MVP 정책)
- 학년/학기는 “과목 자체”가 아니라 “개설(offering)”과 “후기(review)”에서 관리한다.
- 태그는 고정 태그(EVAL_METHOD) + 자유 태그(FREEFORM)로 분리한다.
- 정렬은 최소 3개만 제공:
  - `top_rated`
  - `most_reviewed`
  - `latest`

---

## 10) 개발 우선순위 (2주 내 출시 플랜)
1) DB 스키마 + seed 데이터(전공/과목 일부)
2) 과목 리스트 API + 필터/정렬
3) 과목 상세 + 후기 조회
4) 후기 작성
5) 프론트 최소 UI (리스트/상세/작성)
6) 배포 + 버그 픽스

---

## 11) 금지 사항 / 주의
- DC 게시글 원문을 대량으로 저장/미러링하는 방식은 피한다.
- 스크래핑은 과목 메타데이터 수준으로만 사용하고, 과목은 soft delete/archived로 관리한다.
- MVP에서는 “완벽한 디자인”보다 “빠른 탐색/검색”을 우선한다.
