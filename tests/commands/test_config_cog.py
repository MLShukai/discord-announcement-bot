# tests/commands/test_config_cog.py
"""Tests for the config commands module."""

import re
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord import app_commands

from bot.client import AnnounceBotClient
from bot.commands.config_cog import ConfigCog
from bot.constants import ConfigKeys, Weekday


@pytest.fixture
def mock_bot():
    """Create a mock bot client for testing."""
    bot = MagicMock(spec=AnnounceBotClient)
    bot.config = MagicMock()
    bot.scheduler = MagicMock()

    # Mock confirmation and announcement tasks
    bot.confirmation_task = AsyncMock()
    bot.announcement_task = AsyncMock()

    return bot


@pytest.fixture
def config_cog(mock_bot):
    """Create a ConfigCog instance for testing."""
    return ConfigCog(mock_bot)


@pytest.fixture
def mock_interaction():
    """Create a mock interaction for testing commands."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.roles = []
    return interaction


def test_check_admin_permissions_no_permission(config_cog, mock_interaction):
    """Test permission check when user has no permissions."""
    # Set up roles
    role = MagicMock(spec=discord.Role)
    role.name = "Regular"
    mock_interaction.user.roles = [role]

    # Set up config
    config_cog.bot.config.get.side_effect = lambda section, key, default=None: (
        ["Administrator", "Moderator"]
        if key in (ConfigKeys.KEY_ADMIN_ROLES, ConfigKeys.KEY_MODERATOR_ROLES)
        else default
    )

    # Check permission
    result = config_cog._check_admin_permissions(mock_interaction)
    assert result is False


def test_check_admin_permissions_has_permission(config_cog, mock_interaction):
    """Test permission check when user has permissions."""
    # Set up roles
    role1 = MagicMock(spec=discord.Role)
    role1.name = "Regular"
    role2 = MagicMock(spec=discord.Role)
    role2.name = "Moderator"
    mock_interaction.user.roles = [role1, role2]

    # Set up config
    config_cog.bot.config.get.side_effect = lambda section, key, default=None: (
        ["Administrator", "Moderator"]
        if key in (ConfigKeys.KEY_ADMIN_ROLES, ConfigKeys.KEY_MODERATOR_ROLES)
        else default
    )

    # Check permission
    result = config_cog._check_admin_permissions(mock_interaction)
    assert result is True


@pytest.mark.asyncio
async def test_config_time_confirm_get(config_cog, mock_interaction):
    """Test getting confirm time."""
    # Set up mock
    config_cog.bot.config.get.return_value = "21:30"

    # Call command callback
    await config_cog.config_time_confirm.callback(config_cog, mock_interaction, None)

    # Verify response
    mock_interaction.response.send_message.assert_called_with(
        "現在の確認時刻: 21:30", ephemeral=True
    )


@pytest.mark.asyncio
async def test_config_time_confirm_set_no_permission(config_cog, mock_interaction):
    """Test setting confirm time without permission."""
    # Set up no permission
    with patch.object(config_cog, "_check_admin_permissions", return_value=False):
        # Call command callback
        await config_cog.config_time_confirm.callback(
            config_cog, mock_interaction, "20:00"
        )

        # Verify response
        mock_interaction.response.send_message.assert_called_with(
            "設定を変更する権限がありません。", ephemeral=True
        )


@pytest.mark.asyncio
async def test_config_time_confirm_set_invalid_format(config_cog, mock_interaction):
    """Test setting confirm time with invalid format."""
    # Set up with permission
    with patch.object(config_cog, "_check_admin_permissions", return_value=True):
        # Call command callback with invalid time
        await config_cog.config_time_confirm.callback(
            config_cog, mock_interaction, "25:70"
        )

        # Verify response
        mock_interaction.response.send_message.assert_called_with(
            "無効な時間形式です。HH:MM形式で入力してください。", ephemeral=True
        )


@pytest.mark.asyncio
async def test_config_time_confirm_set_valid(config_cog, mock_interaction):
    """Test setting confirm time with valid data."""
    # Set up with permission
    with (
        patch.object(config_cog, "_check_admin_permissions", return_value=True),
        patch.object(re, "match", return_value=True),
    ):
        config_cog.bot.config.get.return_value = "Thu"

        # Call command callback
        await config_cog.config_time_confirm.callback(
            config_cog, mock_interaction, "20:00"
        )

        # Verify config set
        config_cog.bot.config.set.assert_called_with(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_TIME, "20:00"
        )

        # Verify scheduler called
        config_cog.bot.scheduler.schedule_daily_task.assert_called()

        # Verify response
        mock_interaction.response.send_message.assert_called_with(
            "確認時刻を 20:00 に設定しました。", ephemeral=True
        )


@pytest.mark.asyncio
async def test_config_role_get(config_cog, mock_interaction):
    """Test getting action role."""
    # Set up mock
    config_cog.bot.config.get.return_value = "@TestRole"

    # Call command callback
    await config_cog.config_role.callback(config_cog, mock_interaction, None)

    # Verify response
    mock_interaction.response.send_message.assert_called_with(
        "現在のアクションロール: @TestRole", ephemeral=True
    )


@pytest.mark.asyncio
async def test_config_role_set(config_cog, mock_interaction):
    """Test setting action role."""
    # Set up with permission
    with patch.object(config_cog, "_check_admin_permissions", return_value=True):
        # Create mock role
        role = MagicMock(spec=discord.Role)
        role.name = "TestRole"

        # Call command callback
        await config_cog.config_role.callback(config_cog, mock_interaction, role)

        # Verify config set
        config_cog.bot.config.set.assert_called_with(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ACTION_ROLE, "TestRole"
        )

        # Verify response
        mock_interaction.response.send_message.assert_called_with(
            "アクションロールを TestRole に設定しました。", ephemeral=True
        )


@pytest.mark.asyncio
async def test_config_reset(config_cog, mock_interaction):
    """Test resetting all config values."""
    # Set up with permission
    with patch.object(config_cog, "_check_admin_permissions", return_value=True):
        # Set up mocks
        config_cog.bot.config.get.side_effect = lambda section, key, default=None: {
            ConfigKeys.KEY_CONFIRM_TIME: "21:30",
            ConfigKeys.KEY_CONFIRM_WEEKDAY: "Thu",
            ConfigKeys.KEY_ANNOUNCE_TIME: "21:30",
            ConfigKeys.KEY_ANNOUNCE_WEEKDAY: "Sun",
        }.get(key, default)

        # Call command callback
        await config_cog.config_reset.callback(config_cog, mock_interaction)

        # Verify config reset
        config_cog.bot.config.reset.assert_called_once()

        # Verify scheduler calls
        assert config_cog.bot.scheduler.schedule_daily_task.call_count == 2

        # Verify response
        mock_interaction.response.send_message.assert_called_with(
            "全ての設定をデフォルト値にリセットしました。", ephemeral=True
        )
