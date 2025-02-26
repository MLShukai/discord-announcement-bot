# tests/announcement/test_models.py
"""Tests for the announcement models module."""

import pytest

from bot.announcement.models import LTInfo


def test_lt_info_init_default():
    """Test that LTInfo initializes with expected default values."""
    lt_info = LTInfo()
    assert lt_info.speaker_name is None
    assert lt_info.title is None
    assert lt_info.url is None


def test_lt_info_init_with_values():
    """Test that LTInfo initializes with provided values."""
    lt_info = LTInfo(
        speaker_name="Test Speaker", title="Test Title", url="https://example.com"
    )
    assert lt_info.speaker_name == "Test Speaker"
    assert lt_info.title == "Test Title"
    assert lt_info.url == "https://example.com"


def test_lt_info_is_complete_all_none():
    """Test is_complete property when all attributes are None."""
    lt_info = LTInfo()
    assert lt_info.is_complete is False


def test_lt_info_is_complete_partial():
    """Test is_complete property when some attributes are set."""
    # Only speaker_name is set
    lt_info = LTInfo(speaker_name="Test Speaker")
    assert lt_info.is_complete is False

    # Only title is set
    lt_info = LTInfo(title="Test Title")
    assert lt_info.is_complete is False

    # Two attributes are set
    lt_info = LTInfo(speaker_name="Test Speaker", title="Test Title")
    assert lt_info.is_complete is False


def test_lt_info_is_complete_all_set():
    """Test is_complete property when all attributes are set."""
    lt_info = LTInfo(
        speaker_name="Test Speaker", title="Test Title", url="https://example.com"
    )
    assert lt_info.is_complete is True


def test_lt_info_clear():
    """Test that clear method resets all attributes to None."""
    lt_info = LTInfo(
        speaker_name="Test Speaker", title="Test Title", url="https://example.com"
    )
    lt_info.clear()
    assert lt_info.speaker_name is None
    assert lt_info.title is None
    assert lt_info.url is None


def test_lt_info_str_empty():
    """Test string representation when no attributes are set."""
    lt_info = LTInfo()
    assert str(lt_info) == "LT情報は設定されていません"


def test_lt_info_str_partial():
    """Test string representation when some attributes are set."""
    lt_info = LTInfo(speaker_name="Test Speaker")
    assert "発表者: Test Speaker" in str(lt_info)


def test_lt_info_str_all_set():
    """Test string representation when all attributes are set."""
    lt_info = LTInfo(
        speaker_name="Test Speaker", title="Test Title", url="https://example.com"
    )
    lt_info_str = str(lt_info)
    assert "発表者: Test Speaker" in lt_info_str
    assert "タイトル: Test Title" in lt_info_str
    assert "URL: https://example.com" in lt_info_str
