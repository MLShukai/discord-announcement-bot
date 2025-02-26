# tests/commands/test_manual_cog.py
"""Tests for the manual command module."""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from bot.client import AnnounceBotClient
from bot.commands.manual_cog import ManualCog
from bot.constants import AnnouncementType, ConfigKeys


@pytest.fixture
def mock_bot():
    """Create a mock bot client for testing."""
    bot = MagicMock(spec=AnnounceBotClient)
    bot.config = MagicMock()
    bot.announcement_service = MagicMock()

    return bot


@pytest.fixture
def manual_cog(mock_bot):
    """Create a ManualCog instance for testing."""
    return ManualCog(mock_bot)


@pytest.fixture
def mock_interaction():
    """Create a mock interaction for testing commands."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.roles = []
    return interaction


def test_check_admin_permissions(manual_cog, mock_interaction):
    """Test permission check for admin."""
    # Set up roles
    role1 = MagicMock(spec=discord.Role)
    role1.name = "Regular"
    role2 = MagicMock(spec=discord.Role)
    role2.name = "Moderator"
    mock_interaction.user.roles = [role1, role2]

    # Set up config
    manual_cog.bot.config.get.side_effect = lambda section, key, default=None: (
        ["Administrator", "Moderator"]
        if key in (ConfigKeys.KEY_ADMIN_ROLES, ConfigKeys.KEY_MODERATOR_ROLES)
        else default
    )

    # Check permission
    result = manual_cog._check_admin_permissions(mock_interaction)
    assert result is True


@pytest.mark.asyncio
async def test_manual_confirm_no_permission(manual_cog, mock_interaction):
    """Test manual confirm command without permission."""
    # Set up no permission
    with patch.object(manual_cog, "_check_admin_permissions", return_value=False):
        # Call command callback
        await manual_cog.manual_confirm.callback(manual_cog, mock_interaction)

        # Verify response
        mock_interaction.response.send_message.assert_called_with(
            "このコマンドを実行する権限がありません。", ephemeral=True
        )


@pytest.mark.asyncio
async def test_manual_confirm_no_channel(manual_cog, mock_interaction):
    """Test manual confirm command with no action channel set."""
    # Set up with permission but no channel
    with patch.object(manual_cog, "_check_admin_permissions", return_value=True):
        manual_cog.bot.config.get.return_value = ""

        # Call command callback
        await manual_cog.manual_confirm.callback(manual_cog, mock_interaction)

        # Verify response
        mock_interaction.response.send_message.assert_called_with(
            "アクションチャンネルが設定されていません。`/config channel action` で設定してください。",
            ephemeral=True,
        )


@pytest.mark.asyncio
async def test_manual_confirm_success(manual_cog, mock_interaction):
    """Test manual confirm command with successful execution."""
    # Set up with permission
    with patch.object(manual_cog, "_check_admin_permissions", return_value=True):
        # Set up channel and role mocks
        channel_id = "123456789"
        role_name = "TestRole"
        channel = MagicMock(spec=discord.TextChannel)
        channel.guild = MagicMock()
        channel.mention = "#test-channel"
        role = MagicMock(spec=discord.Role)

        # Set up bot mocks
        manual_cog.bot.config.get.side_effect = lambda section, key, default=None: (
            channel_id
            if key == ConfigKeys.KEY_ACTION_CHANNEL_ID
            else role_name
            if key == ConfigKeys.KEY_ACTION_ROLE
            else default
        )
        manual_cog.bot.get_channel.return_value = channel

        # 重要: AsyncMockを使う
        message = MagicMock(spec=discord.Message)
        send_confirmation_mock = AsyncMock(return_value=message)
        manual_cog.bot.announcement_service.send_confirmation = send_confirmation_mock

        # Set up discord.utils.get
        with patch("discord.utils.get", return_value=role):
            # Call command callback
            await manual_cog.manual_confirm.callback(manual_cog, mock_interaction)

            # Verify service called
            send_confirmation_mock.assert_called_with(channel, role)

            # Verify response
            mock_interaction.followup.send.assert_called_with(
                f"確認メッセージを {channel.mention} に送信しました。", ephemeral=True
            )


@pytest.mark.asyncio
async def test_manual_announce_lt_incomplete(manual_cog, mock_interaction):
    """Test manual announce command with incomplete LT info."""
    # Set up with permission
    with patch.object(manual_cog, "_check_admin_permissions", return_value=True):
        # Set up channel mock
        channel_id = "123456789"
        channel = MagicMock(spec=discord.TextChannel)

        # Set up bot mocks
        manual_cog.bot.config.get.return_value = channel_id
        manual_cog.bot.get_channel.return_value = channel

        # Set up LT info as incomplete
        manual_cog.bot.announcement_service.lt_info.is_complete = False

        # Call command callback
        await manual_cog.manual_announce.callback(manual_cog, mock_interaction, "lt")

        # Verify response about incomplete LT info
        mock_interaction.response.send_message.assert_called_with(
            "LT情報が不完全です。`/lt info` で確認し、`/lt speaker`、`/lt title`、`/lt url` で設定してください。",
            ephemeral=True,
        )


@pytest.mark.asyncio
async def test_manual_announce_success(manual_cog, mock_interaction):
    """Test manual announce command with successful execution."""
    # Set up with permission
    with patch.object(manual_cog, "_check_admin_permissions", return_value=True):
        # Set up channel mock
        channel_id = "123456789"
        channel = MagicMock(spec=discord.TextChannel)
        channel.mention = "#announce-channel"

        # Set up bot mocks
        manual_cog.bot.config.get.return_value = channel_id
        manual_cog.bot.get_channel.return_value = channel

        # 重要: AsyncMockを使う
        message = MagicMock(spec=discord.Message)
        send_announcement_mock = AsyncMock(return_value=message)
        manual_cog.bot.announcement_service.send_announcement = send_announcement_mock

        # LT情報を適切に設定
        manual_cog.bot.announcement_service.lt_info = MagicMock()
        manual_cog.bot.announcement_service.lt_info.is_complete = True

        # Call command callback
        await manual_cog.manual_announce.callback(
            manual_cog, mock_interaction, "regular"
        )

        # Verify service called with correct type
        send_announcement_mock.assert_called()

        # Verify response
        mock_interaction.followup.send.assert_called_with(
            f"regular 告知メッセージを {channel.mention} に送信しました。",
            ephemeral=True,
        )
