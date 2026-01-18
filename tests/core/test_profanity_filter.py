"""Unit tests for profanity filter."""

import pytest

from app.core.profanity_filter import ProfanityFilter


@pytest.fixture
def profanity_filter():
    return ProfanityFilter()


class TestContainsProfanity:
    def test_clean_text_passes(self, profanity_filter):
        assert profanity_filter.contains_profanity("좋은 강의입니다") is False
        assert profanity_filter.contains_profanity("추천합니다") is False

    def test_profanity_detected(self, profanity_filter):
        assert profanity_filter.contains_profanity("시발") is True
        assert profanity_filter.contains_profanity("이 수업 개같음") is True

    def test_profanity_with_spacing(self, profanity_filter):
        assert profanity_filter.contains_profanity("시 발") is True

    def test_empty_string(self, profanity_filter):
        assert profanity_filter.contains_profanity("") is False


class TestFilterText:
    def test_filter_removes_profanity(self, profanity_filter):
        filtered = profanity_filter.filter_text("이 수업 시발 최악")
        assert "시발" not in filtered

    def test_filter_clean_text_unchanged(self, profanity_filter):
        text = "좋은 강의입니다"
        filtered = profanity_filter.filter_text(text)
        assert filtered == text
