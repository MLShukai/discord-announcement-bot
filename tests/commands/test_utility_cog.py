# tests/commands/test_utility_cog.py
"""Tests for the utility commands module."""

import pytest

from bot.commands.utility_cog import UtilityCog
from bot.constants import AnnouncementType
from tests.conftest import make_interaction, make_member


@pytest.fixture
def utility_cog(mock_bot):
    """Create a UtilityCog with a stub bot."""
    return UtilityCog(mock_bot)


@pytest.mark.asyncio
async def test_status_shows_schedule_and_type(utility_cog):
    """Status reports the next announce/event dates and the weekly type."""
    interaction = make_interaction()
    await utility_cog.status.callback(utility_cog, interaction)
    message = interaction.response.send_message.await_args.args[0]
    assert "今週の種別" in message
    assert "6/10" in message  # 次回開催日 (水)


@pytest.mark.asyncio
async def test_help_is_open_to_anyone(utility_cog):
    """Help is available without any role."""
    interaction = make_interaction()
    await utility_cog.help_command.callback(utility_cog, interaction)
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_test_announce_requires_permission(utility_cog):
    """Preview commands require a permission role."""
    interaction = make_interaction(make_member("Member"))
    await utility_cog.test_announce.callback(utility_cog, interaction, None)
    assert "権限" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_test_announce_previews_given_type(utility_cog):
    """Preview renders the announce message for the requested type."""
    interaction = make_interaction(make_member("Moderator"))
    await utility_cog.test_announce.callback(utility_cog, interaction, "workspace")
    message = interaction.response.send_message.await_args.args[0]
    assert "作業会" in message


@pytest.mark.asyncio
async def test_test_open_rest_has_no_message(utility_cog):
    """Preview of open for REST reports there is no message."""
    interaction = make_interaction(make_member("Moderator"))
    await utility_cog.test_open.callback(utility_cog, interaction, "rest")
    message = interaction.response.send_message.await_args.args[0]
    assert "ありません" in message


@pytest.mark.asyncio
async def test_resolve_type_defaults_to_current(utility_cog):
    """A None slug resolves to the current weekly type."""
    utility_cog.bot.state.state.session_type = AnnouncementType.WORKSPACE
    assert utility_cog._resolve_type(None) == AnnouncementType.WORKSPACE
