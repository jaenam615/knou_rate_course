# Design Decisions

This document captures the brainstorming and decision-making process for key architectural choices.

---

## 1. Authentication & Access Control for Reviews

**Date:** 2025-01

**Context:**
The service was initially open to everyone regardless of login status. We wanted to:
1. Require users to be logged in to access the service
2. Require users to write 3 reviews before they can see other reviews/ratings

### Decision: How to Track Review Count?

**Options considered:**

| Approach | Pros | Cons |
|----------|------|------|
| Count on the fly (JOIN/subquery) | Always accurate | Query overhead on every request |
| `review_count` column on User | Fast reads, simple check | Must sync on review create/delete |
| Separate table | N/A | Over-engineered for just a count |

**Decision:** Add `review_count` column to the `users` table.

**Reasoning:**
- The access check happens on *every* protected request - needs to be fast
- Reviews are created/deleted infrequently compared to reads
- The `get_current_user` dependency already fetches the User row for JWT validation, so `user.review_count` comes for free - no additional DB hit
- Simple to maintain: increment on review create, decrement on delete

---

## 2. Is the FastAPI Dependency Enough? (JWT Clarification)

**Concern:** "Should this dependency be enough? No need for JWT/session/cookies?"

**Clarification:** The dependency *uses* JWT under the hood. The flow is:

```
1. POST /login (email, password)
   ↓
2. Server returns JWT token (access_token)
   ↓
3. Frontend stores token & sends it in header:
   Authorization: Bearer <token>
   ↓
4. CurrentUser dependency validates JWT → returns User
```

The `get_current_user` dependency in `app/utils/auth.py` already:
- Extracts JWT from `Authorization` header
- Decodes and validates it
- Fetches the user from DB
- Checks `is_verified`

No additional auth mechanism was needed.

---

## 3. The Chicken-and-Egg Problem

**Concern:** "To WRITE a review, the user needs to access courses, which would display reviews. How can they write their first 3 reviews if they can't see anything?"

**Initial thought:** Blur reviews on the frontend for users with < 3 reviews.

**Counter-concern:** "If the user is smart enough on CS, they can just check devtools to see the reviews. This is stupid. I want actual data protection."

**Decision:** Backend should NOT send data that users shouldn't see.

- Frontend can show whatever UI (blur, warning, prompt)
- But the actual review text and ratings should NOT be in the API response for users with < 3 reviews
- This is real data protection, not just cosmetic

---

## 4. What to Show vs Hide?

**Concern:** "Should users without 3 reviews see ratings? That's all this site provides. But then, would it be too much taken away?"

**Decision:** Show that value *exists* without revealing it:

| Data | < 3 reviews | >= 3 reviews |
|------|-------------|--------------|
| Course list | Visible | Visible |
| Course metadata (name, code, major) | Visible | Visible |
| "This course has 15 reviews" (count) | Visible | Visible |
| Actual ratings (4.2 avg) | Hidden (null) | Visible |
| Review text | Hidden (empty array) | Visible |

**Reasoning:**
- Users need to see courses to write reviews (chicken-and-egg)
- Showing "15 reviews" without the content creates incentive to contribute
- Hiding ratings prevents getting value without contributing

---

## 5. DB Query on Every Request - Is This Normal?

**Concern:** "get_current_user already fetches from DB on every request? Is this normal?"

**Answer:** Yes, it's common and acceptable for most apps.

**Why this is done:**
- Can check if user is banned/deleted in real-time
- Always have fresh user data (like `is_verified`, `review_count`)
- Simple to implement

**Alternative considered:** Store more claims in JWT (stateless, no DB hit)
- **Downside:** Can't invalidate tokens or reflect changes until token expires
- If user writes their 3rd review, their JWT still says `review_count: 2` until re-login

**Decision:** Keep the DB fetch. A simple `SELECT * FROM users WHERE id = ?` on a primary key is sub-millisecond. Postgres can handle thousands per second.

**Future optimization (if needed):** Add Redis caching with short TTL (e.g., 5 min).

---

## Implementation Summary

### Files Changed

1. **`app/models/user.py`**
   - Added `review_count: int` column (default 0)
   - Added `has_full_access` property (`review_count >= 3`)
   - Added `REQUIRED_REVIEWS_FOR_ACCESS = 3` constant

2. **`app/utils/auth.py`**
   - Added `CurrentUserWithFullAccess` dependency (raises 403 if < 3 reviews)

3. **`app/services/review.py`**
   - Increments `user.review_count` when review is created

4. **`app/services/course.py`**
   - `get_list()` and `get_detail()` accept `user` parameter
   - Return `None` for ratings and `[]` for reviews if `!user.has_full_access`

5. **`app/api/v1/courses.py`, `majors.py`, `tags.py`**
   - All endpoints now require `CurrentUser` (must be logged in)

6. **`app/schemas/auth.py`**
   - `UserResponse` includes `review_count` and `has_full_access` for frontend

---

## 6. Trending Searches & Search API

**Date:** 2025-01

**Context:**
Frontend has two features that need backend support:
1. **실시간 검색어 (Trending Searches)** - Shows top 10 trending search terms with rank changes
2. **Search** - Search courses by name

### Decision: Where to Store Trending Data?

**Options considered:**

| Approach | Pros | Cons |
|----------|------|------|
| Postgres | No new dependency | Not ideal for high-frequency increments |
| Redis | Fast increments, built-in sorted sets | New dependency |
| In-memory | Simplest | Lost on restart, no horizontal scaling |

**Decision:** Use Redis for trending searches only.

**Reasoning:**
- Trending needs fast increments (ZINCRBY) on every search
- Redis sorted sets are perfect for "top N" queries (ZREVRANGE)
- Search itself stays in Postgres (simple ILIKE query)
- Redis is optional - if down, trending returns empty, search still works

### Decision: Redis Infrastructure

**Concern:** "Should Redis be in docker-compose or hosted? Do I need a local Redis to mimic production?"

**Decision:** Both.

| Environment | Redis |
|-------------|-------|
| Local (docker-compose) | `redis:7-alpine` |
| Production | Hosted (Upstash, ElastiCache, etc.) |

**Reasoning:**
- Same code, different `REDIS_URL` env var
- Local Redis mimics production behavior exactly
- Upstash free tier (10k commands/day) is enough for MVP
- No "works locally, breaks in prod" surprises

### Decision: Search API - Protecting the DB

**Concern:** "There can be some delay - whatever that doesn't fuck up the DB"

**Options considered:**
1. Rate limiting on endpoint
2. Frontend debounce only
3. Short TTL cache

**Decision:** Rely on frontend debounce + simple safeguards:
- Query minimum length: 2 characters
- Result limit: max 50 results
- Simple ILIKE query (no heavy JOINs)
- If load becomes an issue, add Redis caching later

**Reasoning:**
- Frontend typically debounces search-as-you-type (300ms)
- Backend enforces min length and limits
- ILIKE on indexed column is fast enough for MVP traffic

---

## Implementation Summary (Search & Trending)

### New Files

1. **`app/db/redis.py`** - Redis client connection
2. **`app/services/trending.py`** - Trending search logic
3. **`app/schemas/search.py`** - SearchResult, TrendingItem schemas
4. **`app/api/v1/search.py`** - `/search` and `/trending` endpoints

### Modified Files

1. **`docker-compose.yml`** - Added Redis service
2. **`app/config.py`** - Added `redis_url` setting
3. **`pyproject.toml`** - Added `redis` dependency
4. **`main.py`** - Redis cleanup on shutdown
5. **`app/repositories/course.py`** - Added `search()` method

### Endpoints

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /search?q=` | Required | Search courses, logs to trending |
| `GET /trending` | None | Top 10 trending searches |

---

## 7. Course Evaluation Summary (Aggregated Tags)

**Date:** 2025-01

**Context:**
Tags are bound to individual reviews, but we want to display course-level evaluation info:
- Is the final exam-based (기말시험) or assignment-based (기말과제물)?
- Does it have midterm assignments (중간과제물)?
- Does it have attendance assignments (출석수업과제)?

### Decision: Store as Column or Compute via Query?

**Concern:** "I don't want to add a column to the DB because it would be updated far too often."

**Options considered:**

| Approach | Pros | Cons |
|----------|------|------|
| Denormalized column | Fast reads | Updated on every review create/update/delete |
| GROUP BY query | Always accurate, no sync | Query overhead |
| Cache the GROUP BY | Fast + accurate | Extra complexity |

**Decision:** Use GROUP BY query (compute on-the-fly).

**Reasoning:**
- Query is simple and uses indexed columns
- For single course detail, overhead is negligible
- No sync issues or stale data
- Can add Redis caching later if needed

### Decision: Threshold for Tag Counts

**Concern:** "I don't want just a single review making something appear."

**Decision:** Require more than 3 reviews for `has_midterm` and `has_attendance` to be true.

**Logic:**
```sql
-- Final type: winner between 기말시험 vs 기말과제물
CASE
  WHEN count(기말시험) > count(기말과제물) THEN '기말시험'
  WHEN count(기말과제물) > 0 THEN '기말과제물'
  ELSE NULL
END

-- Midterm/Attendance: need > 3 reviews to count
has_midterm = count(중간과제물) > 3
has_attendance = count(출석수업과제) > 3
```

### Implementation

**New endpoint:** `GET /courses/{id}/eval-summary`

**Response:**
```json
{
  "final_type": "기말시험",
  "has_midterm": true,
  "has_attendance": false
}
```

**Files changed:**
- `app/schemas/course.py` - Added `CourseEvalSummary`
- `app/repositories/course.py` - Added `get_eval_summary()` method
- `app/api/v1/courses.py` - Added endpoint
