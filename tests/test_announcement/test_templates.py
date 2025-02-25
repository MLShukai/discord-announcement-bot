"""Tests for the templates module."""

import datetime

import pytest

from bot.announcement.templates import AnnouncementTemplates


class TestAnnouncementTemplates:
    """Tests for the AnnouncementTemplates class."""

    def test_format_regular(self):
        """Test formatting a regular meeting announcement."""
        date = datetime.date(2023, 5, 15)  # May 15, 2023
        url = "https://example.com"

        message = AnnouncementTemplates.format_regular(date, url)

        assert "今週の5/15のML集会も21時半より開催致します。" in message
        assert "今週はまったり雑談会です" in message
        assert "5/15" in message  # Date should be formatted as 5/15
        assert url in message

    def test_format_lightning_talk(self):
        """Test formatting a lightning talk meeting announcement."""
        date = datetime.date(2023, 6, 20)  # June 20, 2023
        speaker = "テスト太郎"
        title = "テストLT発表"
        url = "https://example.com/lt"

        message = AnnouncementTemplates.format_lightning_talk(date, speaker, title, url)

        assert "今週のML集会はLT会!" in message
        assert "6/20の21時半より開催致します。" in message
        assert f"{speaker}さんより「{title}」を行いますので" in message
        assert "ぜひみなさんお越しください！" in message
        assert url in message

    def test_format_rest(self):
        """Test formatting a canceled meeting announcement."""
        message = AnnouncementTemplates.format_rest()

        assert message == "今週のML集会はおやすみです。"
