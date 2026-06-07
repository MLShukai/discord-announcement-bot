# tests/state/test_store.py
"""Tests for the persistent state store."""

import datetime

from bot.constants import AnnouncementType
from bot.state import LTInfo, SessionState, StateStore


def test_lt_info_is_complete_and_clear():
    """LTInfo reports completeness and clears all fields."""
    lt = LTInfo(speaker_name="山田", title="入門", url="https://example.com")
    assert lt.is_complete is True

    lt.url = None
    assert lt.is_complete is False

    lt.clear()
    assert lt.speaker_name is None
    assert lt.title is None
    assert lt.url is None


def test_default_state_when_file_missing(tmp_path):
    """A missing state file yields default state."""
    store = StateStore(str(tmp_path / "absent.json"))
    assert store.state.session_type == AnnouncementType.REGULAR
    assert store.state.lt.is_complete is False
    assert store.state.announce_message_id is None
    assert store.state.confirm_message_id is None
    assert store.state.target_event_date is None


def test_save_and_reload_roundtrip(tmp_path):
    """State survives a save/load roundtrip across store instances."""
    path = tmp_path / "state.json"
    store = StateStore(str(path))
    store.state.session_type = AnnouncementType.LIGHTNING_TALK
    store.state.lt = LTInfo(speaker_name="鈴木", title="強化学習", url="https://x")
    store.state.announce_message_id = 99887766
    store.state.confirm_message_id = 11223344
    store.state.target_event_date = datetime.date(2026, 6, 10)
    store.save()

    reloaded = StateStore(str(path))
    assert reloaded.state.session_type == AnnouncementType.LIGHTNING_TALK
    assert reloaded.state.lt.speaker_name == "鈴木"
    assert reloaded.state.lt.title == "強化学習"
    assert reloaded.state.lt.url == "https://x"
    assert reloaded.state.announce_message_id == 99887766
    assert reloaded.state.confirm_message_id == 11223344
    assert reloaded.state.target_event_date == datetime.date(2026, 6, 10)


def test_from_dict_falls_back_on_unknown_type():
    """Unknown session_type falls back to REGULAR."""
    state = SessionState.from_dict({"session_type": "NOPE"})
    assert state.session_type == AnnouncementType.REGULAR


def test_corrupt_file_yields_default_state(tmp_path):
    """A corrupt JSON file does not crash; defaults are used."""
    path = tmp_path / "state.json"
    path.write_text("{ not json", encoding="utf-8")
    store = StateStore(str(path))
    assert store.state.session_type == AnnouncementType.REGULAR
