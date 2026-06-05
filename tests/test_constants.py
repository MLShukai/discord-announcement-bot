# tests/test_constants.py
"""Tests for the constants module."""

from bot.constants import (
    REACTION_TO_TYPE,
    SLUG_BY_TYPE,
    TYPE_BY_SLUG,
    AnnouncementType,
    ReactionEmoji,
    Weekday,
)


def test_weekday_to_int():
    """Test converting weekday strings to integers."""
    assert Weekday.to_int(Weekday.MONDAY) == 0
    assert Weekday.to_int(Weekday.WEDNESDAY) == 2
    assert Weekday.to_int(Weekday.SUNDAY) == 6
    assert Weekday.to_int("InvalidDay") == 6  # 未知は日曜


def test_weekday_to_jp():
    """Test converting weekday integers to Japanese characters."""
    assert Weekday.to_jp(0) == "月"
    assert Weekday.to_jp(2) == "水"
    assert Weekday.to_jp(6) == "日"
    assert Weekday.to_jp(7) == "月"  # 範囲外はラップ
    assert Weekday.to_jp(-1) == "日"


def test_announcement_type_string_representation():
    """Test string representation of AnnouncementType enum."""
    assert str(AnnouncementType.REGULAR) == "通常開催"
    assert str(AnnouncementType.LIGHTNING_TALK) == "LT開催"
    assert str(AnnouncementType.WORKSPACE) == "作業部屋開催"
    assert str(AnnouncementType.REST) == "おやすみ"


def test_reaction_emoji_constants():
    """Test ReactionEmoji constants have expected values."""
    assert ReactionEmoji.REGULAR == "👍"
    assert ReactionEmoji.LIGHTNING_TALK == "⚡"
    assert ReactionEmoji.WORKSPACE == "🛠️"
    assert ReactionEmoji.REST == "💤"


def test_reaction_to_type_mapping():
    """Each reaction emoji maps to its announcement type."""
    assert REACTION_TO_TYPE[ReactionEmoji.REGULAR] == AnnouncementType.REGULAR
    assert (
        REACTION_TO_TYPE[ReactionEmoji.LIGHTNING_TALK]
        == AnnouncementType.LIGHTNING_TALK
    )
    assert REACTION_TO_TYPE[ReactionEmoji.WORKSPACE] == AnnouncementType.WORKSPACE
    assert REACTION_TO_TYPE[ReactionEmoji.REST] == AnnouncementType.REST


def test_slug_type_roundtrip():
    """Slug <-> type mappings are consistent for every type."""
    assert TYPE_BY_SLUG["lt"] == AnnouncementType.LIGHTNING_TALK
    assert TYPE_BY_SLUG["workspace"] == AnnouncementType.WORKSPACE
    for announcement_type in AnnouncementType:
        slug = SLUG_BY_TYPE[announcement_type]
        assert TYPE_BY_SLUG[slug] == announcement_type
