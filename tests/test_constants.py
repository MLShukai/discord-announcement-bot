# tests/test_constants.py
"""Tests for the constants module."""

from bot.constants import AnnouncementType, ReactionEmoji, Weekday


def test_weekday_to_int():
    """Test converting weekday strings to integers."""
    assert Weekday.to_int(Weekday.MONDAY) == 0
    assert Weekday.to_int(Weekday.TUESDAY) == 1
    assert Weekday.to_int(Weekday.WEDNESDAY) == 2
    assert Weekday.to_int(Weekday.THURSDAY) == 3
    assert Weekday.to_int(Weekday.FRIDAY) == 4
    assert Weekday.to_int(Weekday.SATURDAY) == 5
    assert Weekday.to_int(Weekday.SUNDAY) == 6

    # Test with invalid input
    assert Weekday.to_int("InvalidDay") == 6  # Should default to Sunday (6)


def test_weekday_to_jp():
    """Test converting weekday integers to Japanese characters."""
    assert Weekday.to_jp(0) == "月"
    assert Weekday.to_jp(1) == "火"
    assert Weekday.to_jp(2) == "水"
    assert Weekday.to_jp(3) == "木"
    assert Weekday.to_jp(4) == "金"
    assert Weekday.to_jp(5) == "土"
    assert Weekday.to_jp(6) == "日"

    # Test with values outside normal range
    assert Weekday.to_jp(7) == "月"  # Should wrap around to Monday
    assert Weekday.to_jp(-1) == "日"  # Should wrap to Sunday


def test_announcement_type_string_representation():
    """Test string representation of AnnouncementType enum."""
    assert str(AnnouncementType.REGULAR) == "通常開催"
    assert str(AnnouncementType.LIGHTNING_TALK) == "LT開催"
    assert str(AnnouncementType.REST) == "おやすみ"


def test_reaction_emoji_constants():
    """Test ReactionEmoji constants have expected values."""
    assert ReactionEmoji.REGULAR == "👍"
    assert ReactionEmoji.LIGHTNING_TALK == "⚡"
    assert ReactionEmoji.REST == "💤"
