# tests/commands/test_session_cog.py
"""Tests for the session commands module (/plan, /open, /manual)."""

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from bot.commands.session_cog import SessionCog
from bot.constants import AnnouncementType
from bot.state import LTInfo
from tests.conftest import make_interaction, make_member


@pytest.fixture
def session_cog(mock_bot):
    """Create a SessionCog with a stub bot."""
    return SessionCog(mock_bot)


@pytest.mark.asyncio
async def test_plan_set_requires_permission(session_cog):
    """A user without a role cannot change the plan."""
    interaction = make_interaction(make_member("Member"))
    await session_cog.plan_set.callback(session_cog, interaction, "lt")
    assert session_cog.bot.state.state.session_type == AnnouncementType.REGULAR


@pytest.mark.asyncio
async def test_plan_set_updates_session_type(session_cog):
    """A moderator sets the weekly type and it is persisted."""
    interaction = make_interaction(make_member("Moderator"))
    await session_cog.plan_set.callback(session_cog, interaction, "workspace")
    assert session_cog.bot.state.state.session_type == AnnouncementType.WORKSPACE


@pytest.mark.asyncio
async def test_plan_set_lt_warns_when_incomplete(session_cog):
    """Setting LT with incomplete info warns the user."""
    interaction = make_interaction(make_member("Moderator"))
    await session_cog.plan_set.callback(session_cog, interaction, "lt")
    assert session_cog.bot.state.state.session_type == AnnouncementType.LIGHTNING_TALK
    assert "不完全" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_plan_set_invalid_type(session_cog):
    """An invalid slug is rejected."""
    interaction = make_interaction(make_member("Moderator"))
    await session_cog.plan_set.callback(session_cog, interaction, "party")
    assert "無効な種別" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_open_rest_warns_and_sends_nothing(session_cog):
    """/open on a REST week warns and posts nothing."""
    session_cog.bot.state.state.session_type = AnnouncementType.REST
    interaction = make_interaction(make_member("Moderator"))
    await session_cog.open_command.callback(session_cog, interaction)
    assert "おやすみ" in interaction.response.send_message.await_args.args[0]
    session_cog.bot.get_announce_channel.assert_not_called()


@pytest.mark.asyncio
async def test_open_lt_incomplete_warns(session_cog):
    """/open on an LT week without complete info warns."""
    session_cog.bot.state.state.session_type = AnnouncementType.LIGHTNING_TALK
    interaction = make_interaction(make_member("Moderator"))
    await session_cog.open_command.callback(session_cog, interaction)
    assert "不完全" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_open_regular_posts(session_cog):
    """/open on a regular week posts the open message."""
    session_cog.bot.state.state.session_type = AnnouncementType.REGULAR
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "announce"
    channel.mention = "#announce"
    channel.send = AsyncMock(return_value=MagicMock(spec=discord.Message))
    session_cog.bot.get_announce_channel.return_value = channel

    interaction = make_interaction(make_member("Moderator"))
    await session_cog.open_command.callback(session_cog, interaction)

    channel.send.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_open_lt_complete_posts(session_cog):
    """/open on an LT week with complete info posts."""
    session_cog.bot.state.state.session_type = AnnouncementType.LIGHTNING_TALK
    session_cog.bot.state.state.lt = LTInfo(
        speaker_name="山田", title="T", url="https://x"
    )
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "announce"
    channel.mention = "#announce"
    channel.send = AsyncMock(return_value=MagicMock(spec=discord.Message))
    session_cog.bot.get_announce_channel.return_value = channel

    interaction = make_interaction(make_member("Moderator"))
    await session_cog.open_command.callback(session_cog, interaction)

    channel.send.assert_awaited_once()
