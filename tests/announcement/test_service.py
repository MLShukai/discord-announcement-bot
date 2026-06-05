# tests/announcement/test_service.py
"""Tests for the announcement service module."""

import datetime
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from bot.constants import AnnouncementType
from bot.state import LTInfo


def test_next_event_date_is_upcoming_wednesday(service):
    """With the fixed Sunday clock, the next event date is the next
    Wednesday."""
    # FIXED_NOW = 2026-06-07 (Sun), event_weekday = Wed -> 2026-06-10
    assert service.next_event_date() == datetime.date(2026, 6, 10)


def test_build_announce_regular_has_date_and_legend(service):
    """Regular announce embeds the event date and appends the reaction
    legend."""
    content = service.build_announce(AnnouncementType.REGULAR)
    assert "6/10" in content
    assert "(水)" in content
    assert "21:30" in content
    # リアクション凡例が付与される
    assert "👍" in content and "⚡" in content and "🛠️" in content and "💤" in content


def test_build_announce_lightning_talk_embeds_speaker_and_title(service):
    """LT announce embeds speaker and title from state."""
    service.state.state.lt = LTInfo(
        speaker_name="山田", title="強化学習入門", url="https://x"
    )
    content = service.build_announce(AnnouncementType.LIGHTNING_TALK)
    assert "山田" in content
    assert "強化学習入門" in content


def test_build_announce_workspace(service):
    """Workspace announce renders without speaker/title."""
    content = service.build_announce(AnnouncementType.WORKSPACE)
    assert "作業会" in content


def test_build_open_regular(service):
    """Open message for regular renders instance-open text."""
    content = service.build_open(AnnouncementType.REGULAR)
    assert content is not None
    assert "インスタンス" in content


def test_build_open_rest_returns_none(service):
    """REST has no open message."""
    assert service.build_open(AnnouncementType.REST) is None


def test_build_open_lightning_talk_embeds_speaker(service):
    """Open message for LT embeds the speaker."""
    service.state.state.lt = LTInfo(speaker_name="鈴木", title="T", url="https://x")
    content = service.build_open(AnnouncementType.LIGHTNING_TALK)
    assert content is not None
    assert "鈴木" in content


@pytest.mark.asyncio
async def test_send_announce_adds_reactions_and_persists_message_id(service):
    """send_announce posts, adds 4 reactions, and stores the message id."""
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "announce"
    sent = MagicMock(spec=discord.Message)
    sent.id = 4242
    channel.send = AsyncMock(return_value=sent)

    result = await service.send_announce(channel)

    assert result is sent
    channel.send.assert_awaited_once()
    assert sent.add_reaction.await_count == 4
    assert service.state.state.announce_message_id == 4242
    assert service.state.state.target_event_date == datetime.date(2026, 6, 10)


@pytest.mark.asyncio
async def test_send_open_rest_sends_nothing(service):
    """send_open does not post when the week is REST."""
    service.state.state.session_type = AnnouncementType.REST
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "announce"
    channel.send = AsyncMock()

    result = await service.send_open(channel)

    assert result is None
    channel.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_open_regular_posts(service):
    """send_open posts the open message for a non-REST week."""
    service.state.state.session_type = AnnouncementType.REGULAR
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "announce"
    channel.send = AsyncMock(return_value=MagicMock(spec=discord.Message))

    result = await service.send_open(channel)

    assert result is not None
    channel.send.assert_awaited_once()
