# tests/commands/test_config_cog.py
"""Tests for the config commands module."""

import pytest

from bot.commands.config_cog import ConfigCog
from bot.constants import ConfigKeys
from tests.conftest import make_interaction, make_member


@pytest.fixture
def config_cog(mock_bot):
    """Create a ConfigCog with a stub bot."""
    return ConfigCog(mock_bot)


@pytest.mark.asyncio
async def test_announce_requires_permission(config_cog):
    """A user without a role cannot change the schedule."""
    interaction = make_interaction(make_member("Member"))
    await config_cog.config_announce.callback(config_cog, interaction, "Sun", "12:00")
    # 既定のまま変更されない
    assert (
        config_cog.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY
        )
        == "Sun"
    )
    assert "権限" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_announce_sets_weekday_and_time(config_cog):
    """A moderator can set the announce schedule and reschedules the task."""
    interaction = make_interaction(make_member("Moderator"))
    await config_cog.config_announce.callback(config_cog, interaction, "Mon", "09:30")
    cfg = config_cog.bot.config
    assert (
        cfg.get(ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY) == "Mon"
    )
    assert cfg.get(ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME) == "09:30"
    config_cog.bot.schedule_announce_task.assert_called_once()


@pytest.mark.asyncio
async def test_announce_rejects_invalid_day(config_cog):
    """An invalid weekday is rejected."""
    interaction = make_interaction(make_member("Moderator"))
    await config_cog.config_announce.callback(
        config_cog, interaction, "Funday", "12:00"
    )
    assert "無効な曜日" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_announce_rejects_invalid_time(config_cog):
    """An invalid time format is rejected."""
    interaction = make_interaction(make_member("Moderator"))
    await config_cog.config_announce.callback(config_cog, interaction, "Sun", "25:99")
    assert "無効な時間" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_event_sets_event_schedule(config_cog):
    """A moderator can set the event weekday/time."""
    interaction = make_interaction(make_member("告知管理者"))
    await config_cog.config_event.callback(config_cog, interaction, "Thu", "20:00")
    cfg = config_cog.bot.config
    assert cfg.get(ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_EVENT_WEEKDAY) == "Thu"
    assert cfg.get(ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_EVENT_TIME) == "20:00"
