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


def test_build_announce_regular_has_date_without_legend(service):
    """Regular announce embeds the event date and does NOT append a legend.

    リアクション凡例・絵文字は確認チャンネルの報告へ移したため、公開告知本文には付かない。
    """
    content = service.build_announce(AnnouncementType.REGULAR)
    assert "6/10" in content
    assert "(水)" in content
    assert "21:30" in content
    # 公開告知本文にはリアクション凡例を付けない
    assert "👍" not in content
    assert "変更する場合" not in content


def test_build_confirm_has_type_and_legend(service):
    """Confirm report names the current type and includes the reaction
    legend."""
    content = service.build_confirm(AnnouncementType.REGULAR)
    assert "通常開催" in content
    assert "変更する場合" in content
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
async def test_send_announce_no_reactions_and_persists_message_id(service):
    """send_announce posts without reactions and stores the message id."""
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "announce"
    sent = MagicMock(spec=discord.Message)
    sent.id = 4242
    channel.send = AsyncMock(return_value=sent)

    result = await service.send_announce(channel)

    assert result is sent
    channel.send.assert_awaited_once()
    # 公開告知にはリアクションを付与しない
    sent.add_reaction.assert_not_called()
    assert service.state.state.announce_message_id == 4242
    assert service.state.state.target_event_date == datetime.date(2026, 6, 10)


@pytest.mark.asyncio
async def test_send_confirm_adds_reactions_and_persists_confirm_id(service):
    """send_confirm posts a mentioned report, adds 4 reactions, stores the
    id."""
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "confirm"
    sent = MagicMock(spec=discord.Message)
    sent.id = 7777
    channel.send = AsyncMock(return_value=sent)

    result = await service.send_confirm(channel, mention="@告知管理者")

    assert result is sent
    channel.send.assert_awaited_once()
    # メンションが本文先頭に付く
    assert channel.send.await_args.args[0].startswith("@告知管理者")
    assert sent.add_reaction.await_count == 4
    assert service.state.state.confirm_message_id == 7777


@pytest.mark.asyncio
async def test_reannounce_deletes_old_and_reposts_new_type(service):
    """Reannounce deletes the prior public message and reposts the current
    type."""
    service.state.state.announce_message_id = 1000
    service.state.state.session_type = AnnouncementType.WORKSPACE

    old_message = MagicMock(spec=discord.Message)
    old_message.delete = AsyncMock()
    new_message = MagicMock(spec=discord.Message)
    new_message.id = 2000
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "announce"
    channel.fetch_message = AsyncMock(return_value=old_message)
    channel.send = AsyncMock(return_value=new_message)

    result = await service.reannounce(channel)

    channel.fetch_message.assert_awaited_once_with(1000)
    old_message.delete.assert_awaited_once()
    assert "作業会" in channel.send.await_args.args[0]
    assert result is new_message
    assert service.state.state.announce_message_id == 2000


@pytest.mark.asyncio
async def test_reannounce_noop_without_prior_announce(service):
    """Reannounce does nothing when no public announcement exists yet."""
    service.state.state.announce_message_id = None
    channel = MagicMock(spec=discord.TextChannel)
    channel.send = AsyncMock()
    channel.fetch_message = AsyncMock()

    result = await service.reannounce(channel)

    assert result is None
    channel.fetch_message.assert_not_awaited()
    channel.send.assert_not_awaited()


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
