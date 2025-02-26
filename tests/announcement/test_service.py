# tests/announcement/test_service.py
"""Tests for the announcement service module."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from bot.announcement.models import LTInfo
from bot.announcement.service import AnnouncementService
from bot.config import ConfigManager
from bot.constants import AnnouncementType


@pytest.fixture
def mock_config():
    """Create a mock ConfigManager for testing."""
    config = MagicMock(spec=ConfigManager)

    # Set up common config.get return values
    def get_side_effect(section, key, default=None):
        if section == "settings" and key == "default_url":
            return "https://example.com"
        if section == "templates" and key == "regular":
            return "今週の$mm/$ddのML集会も21時半より開催致します。今週はまったり雑談会です\n$url"
        if section == "templates" and key == "lightning_talk":
            return "今週のML集会はLT会! $mm/$ddの21時半より開催致します。\n$speaker_nameさんより「$title」を行いますので、ぜひみなさんお越しください！\n$url"
        if section == "templates" and key == "rest":
            return "今週のML集会はおやすみです。"
        if section == "templates" and key == "confirmation":
            return "$role 今度の日曜 ($month/$day) の予定を確認します。"
        if section == "settings" and key == "announce_weekday":
            return "Sun"
        return default

    config.get.side_effect = get_side_effect
    return config


@pytest.fixture
def announcement_service(mock_config):
    """Create an AnnouncementService for testing."""
    return AnnouncementService(mock_config)


def test_announcement_service_init(mock_config):
    """Test AnnouncementService initialization."""
    service = AnnouncementService(mock_config)
    assert service.config == mock_config
    assert isinstance(service.lt_info, LTInfo)


def test_lt_properties(announcement_service):
    """Test LT getter and setter properties."""
    # Test initial values
    assert announcement_service.lt_speaker is None
    assert announcement_service.lt_title is None
    assert announcement_service.lt_url is None

    # Test setters
    announcement_service.lt_speaker = "Test Speaker"
    announcement_service.lt_title = "Test Title"
    announcement_service.lt_url = "https://test.com"

    # Test getters after setting
    assert announcement_service.lt_speaker == "Test Speaker"
    assert announcement_service.lt_title == "Test Title"
    assert announcement_service.lt_url == "https://test.com"


def test_get_next_weekday(announcement_service):
    """Test getting the next date for a specified weekday."""
    today = datetime.date.today()

    for weekday_str, weekday_num in [
        ("Mon", 0),
        ("Tue", 1),
        ("Wed", 2),
        ("Thu", 3),
        ("Fri", 4),
        ("Sat", 5),
        ("Sun", 6),
    ]:
        next_date = announcement_service.get_next_weekday(weekday_str)

        # Check if result is a date
        assert isinstance(next_date, datetime.date)

        # Check if the date is in the future
        assert next_date >= today

        # Check if the weekday matches
        assert next_date.weekday() == weekday_num

        # Check if the date is within the next 7 days
        assert (next_date - today).days < 8


def test_generate_announcement_regular(announcement_service):
    """Test generating a regular announcement message."""
    test_date = datetime.date(2023, 5, 15)  # Use a fixed date for testing

    message = announcement_service.generate_announcement_content(
        AnnouncementType.REGULAR, test_date
    )

    # Check for expected content
    assert "5/15" in message  # Month/day
    assert "集会も21時半より開催" in message  # Time
    assert "https://example.com" in message  # Default URL


def test_generate_announcement_lt(announcement_service):
    """Test generating a lightning talk announcement message."""
    test_date = datetime.date(2023, 5, 15)

    # Set LT info
    announcement_service.lt_speaker = "Test Speaker"
    announcement_service.lt_title = "Test Title"
    announcement_service.lt_url = "https://lt-test.com"

    message = announcement_service.generate_announcement_content(
        AnnouncementType.LIGHTNING_TALK, test_date
    )

    # Check for expected content
    assert "5/15" in message  # Month/day
    assert "LT会" in message
    assert "Test Speaker" in message
    assert "「Test Title」" in message
    assert "https://lt-test.com" in message


def test_generate_announcement_lt_incomplete(announcement_service):
    """Test generating LT announcement with incomplete info."""
    test_date = datetime.date(2023, 5, 15)

    # Set only speaker name
    announcement_service.lt_speaker = "Test Speaker"

    message = announcement_service.generate_announcement_content(
        AnnouncementType.LIGHTNING_TALK, test_date
    )

    # Check for placeholder values
    assert "Test Speaker" in message
    assert "タイトル未定" in message
    assert "https://example.com" in message  # Default URL


def test_generate_announcement_rest(announcement_service):
    """Test generating a rest announcement message."""
    message = announcement_service.generate_announcement_content(AnnouncementType.REST)

    assert message == "今週のML集会はおやすみです。"


@pytest.mark.asyncio
async def test_send_announcement(announcement_service):
    """Test sending an announcement message."""
    # Create mock channel
    mock_channel = AsyncMock(spec=discord.TextChannel)
    mock_channel.send.return_value = MagicMock(spec=discord.Message)

    # Set test data
    announcement_service.lt_info.speaker_name = "Test Speaker"
    announcement_service.lt_info.title = "Test Title"
    announcement_service.lt_info.url = "https://test.com"

    # Test sending each type of announcement
    for announcement_type in AnnouncementType:
        # Reset mocks
        mock_channel.reset_mock()

        # Send announcement
        result = await announcement_service.send_announcement(
            mock_channel, announcement_type
        )

        # Verify channel.send was called
        assert mock_channel.send.called

        # Verify result is the mock message
        assert result == mock_channel.send.return_value

        # If it was a LT announcement, verify info was cleared
        if announcement_type == AnnouncementType.LIGHTNING_TALK:
            assert announcement_service.lt_speaker is None
            assert announcement_service.lt_title is None
            assert announcement_service.lt_url is None


@pytest.mark.asyncio
async def test_send_announcement_channel_none(announcement_service):
    """Test sending an announcement with None channel."""
    result = await announcement_service.send_announcement(
        None, AnnouncementType.REGULAR
    )
    assert result is None


@pytest.mark.asyncio
async def test_send_announcement_exception(announcement_service):
    """Test sending an announcement with exception."""
    mock_channel = AsyncMock(spec=discord.TextChannel)
    mock_channel.send.side_effect = discord.DiscordException("Test error")

    result = await announcement_service.send_announcement(
        mock_channel, AnnouncementType.REGULAR
    )
    assert result is None


@pytest.mark.asyncio
async def test_send_confirmation(announcement_service):
    """Test sending a confirmation message."""
    # Create mock channel and role
    mock_channel = AsyncMock(spec=discord.TextChannel)
    mock_message = MagicMock(spec=discord.Message)
    mock_channel.send.return_value = mock_message

    mock_role = MagicMock(spec=discord.Role)
    mock_role.mention = "@TestRole"

    # Send confirmation
    result = await announcement_service.send_confirmation(mock_channel, mock_role)

    # Verify channel.send was called
    assert mock_channel.send.called

    # Verify role mention was used
    call_args = mock_channel.send.call_args[0][0]
    assert "@TestRole" in call_args

    # Verify reactions were added
    assert mock_message.add_reaction.call_count == 3

    # Verify result is the mock message
    assert result == mock_message


@pytest.mark.asyncio
async def test_send_confirmation_channel_none(announcement_service):
    """Test sending a confirmation with None channel."""
    result = await announcement_service.send_confirmation(None)
    assert result is None


@pytest.mark.asyncio
async def test_send_confirmation_exception(announcement_service):
    """Test sending a confirmation with exception."""
    mock_channel = AsyncMock(spec=discord.TextChannel)
    mock_channel.send.side_effect = discord.DiscordException("Test error")

    result = await announcement_service.send_confirmation(mock_channel)
    assert result is None
