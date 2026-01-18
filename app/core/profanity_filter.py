# app/services/profanity_filter.py
import re
from dataclasses import dataclass

DEFAULT_BANNED_WORDS = [
    # TODO: 확장
    "시발", "씨발", "ㅅㅂ",
    "병신", "ㅂㅅ",
    "좆",
    "존나",
    "개새끼", "새끼",
]


def normalize_text(text: str) -> str:
    """
    비속어 탐지용 정규화
    - 소문자화
    - 공백 제거
    - 특수문자 제거
    - 반복 문자 축약
    """
    if not text:
        return ""

    t = text.lower()
    t = re.sub(r"\s+", "", t)
    t = re.sub(r"[^0-9a-z가-힣ㄱ-ㅎㅏ-ㅣ]", "", t)
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)
    return t


@dataclass(frozen=True)
class ProfanityResult:
    has_profanity: bool
    matched_word: str | None = None


class ProfanityFilter:
    def __init__(self, banned_words: list[str] | None = None):
        self.banned_words = banned_words or DEFAULT_BANNED_WORDS
        self._patterns = [re.compile(re.escape(w)) for w in self.banned_words if w]

    def check(self, text: str) -> ProfanityResult:
        normalized = normalize_text(text)

        for w, pat in zip(self.banned_words, self._patterns):
            if pat.search(normalized):
                return ProfanityResult(True, matched_word=w)

        return ProfanityResult(False)
