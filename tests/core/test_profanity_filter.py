"""Unit tests for profanity filter."""

import pytest

from app.core.profanity_filter import ProfanityFilter


@pytest.fixture
def profanity_filter():
    return ProfanityFilter()


class TestCheck:
    def test_clean_text_passes(self, profanity_filter):
        result = profanity_filter.check("좋은 강의입니다")
        assert result.has_profanity is False
        assert result.matched_word is None

        result = profanity_filter.check("추천합니다")
        assert result.has_profanity is False

    def test_profanity_detected(self, profanity_filter):
        result = profanity_filter.check("시발")
        assert result.has_profanity is True
        assert result.matched_word == "시발"

        result = profanity_filter.check("이 수업 병신같음")
        assert result.has_profanity is True

    def test_profanity_with_spacing(self, profanity_filter):
        # normalize_text removes spaces, so "시 발" becomes "시발"
        result = profanity_filter.check("시 발")
        assert result.has_profanity is True

    def test_empty_string(self, profanity_filter):
        result = profanity_filter.check("")
        assert result.has_profanity is False

    def test_profanity_with_special_chars(self, profanity_filter):
        # normalize_text removes special characters
        result = profanity_filter.check("시.발")
        assert result.has_profanity is True

    def test_partial_match(self, profanity_filter):
        # Should detect profanity even when part of longer text
        result = profanity_filter.check("진짜 시발 짜증나네")
        assert result.has_profanity is True


class TestCustomBannedWords:
    def test_custom_banned_words(self):
        custom_filter = ProfanityFilter(banned_words=["테스트", "금지어"])

        result = custom_filter.check("테스트 단어")
        assert result.has_profanity is True
        assert result.matched_word == "테스트"

    def test_empty_banned_words_uses_defaults(self):
        # Empty list is falsy, so it falls back to DEFAULT_BANNED_WORDS
        custom_filter = ProfanityFilter(banned_words=[])

        result = custom_filter.check("시발")  # Default banned word
        assert result.has_profanity is True  # Still detected because [] is falsy -> uses defaults

    def test_none_uses_defaults(self):
        # None also falls back to DEFAULT_BANNED_WORDS
        custom_filter = ProfanityFilter(banned_words=None)

        result = custom_filter.check("시발")
        assert result.has_profanity is True
