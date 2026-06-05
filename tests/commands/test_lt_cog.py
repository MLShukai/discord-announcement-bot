# tests/commands/test_lt_cog.py
"""Tests for the LT commands module."""

import pytest

from bot.commands.lt_cog import LtCog
from tests.conftest import make_interaction, make_member


@pytest.fixture
def lt_cog(mock_bot):
    """Create an LtCog with a stub bot."""
    return LtCog(mock_bot)


@pytest.mark.asyncio
async def test_speaker_getter_is_open_to_anyone(lt_cog):
    """The getter works without any permission role."""
    interaction = make_interaction()  # ロール無し
    await lt_cog.lt_speaker.callback(lt_cog, interaction, None)
    interaction.response.send_message.assert_awaited_once()
    assert "未設定" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_speaker_setter_requires_permission(lt_cog):
    """Setting the speaker without a role is rejected and not persisted."""
    interaction = make_interaction(make_member("Member"))
    await lt_cog.lt_speaker.callback(lt_cog, interaction, "山田")
    assert lt_cog.bot.state.state.lt.speaker_name is None
    assert "権限" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_lt_set_persists_to_state(lt_cog):
    """A moderator can set LT info and it is stored in state."""
    interaction = make_interaction(make_member("Moderator"))
    await lt_cog.lt_set.callback(
        lt_cog, interaction, "強化学習入門", "山田", "https://x"
    )
    lt = lt_cog.bot.state.state.lt
    assert lt.title == "強化学習入門"
    assert lt.speaker_name == "山田"
    assert lt.url == "https://x"


@pytest.mark.asyncio
async def test_lt_set_lt_admin_role_allowed(lt_cog):
    """The lt_admin role may edit LT info."""
    interaction = make_interaction(make_member("LT管理者"))
    await lt_cog.lt_set.callback(lt_cog, interaction, "T", "S", None)
    assert lt_cog.bot.state.state.lt.title == "T"


@pytest.mark.asyncio
async def test_lt_clear_resets_info(lt_cog):
    """Clearing removes all LT info."""
    lt_cog.bot.state.state.lt.speaker_name = "x"
    interaction = make_interaction(make_member("Administrator"))
    await lt_cog.lt_clear.callback(lt_cog, interaction)
    assert lt_cog.bot.state.state.lt.speaker_name is None
