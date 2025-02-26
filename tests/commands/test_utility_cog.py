# tests/commands/test_utility_cog.py
"""Tests for the utility commands module."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from bot.client import AnnounceBotClient
from bot.commands.utility_cog import UtilityCog
from bot.constants import ConfigKeys, Weekday


@pytest.fixture
def mock_bot():
    """Create a mock bot client for testing."""
    bot = MagicMock(spec=AnnounceBotClient)
    bot.config = MagicMock()
    bot.announcement_service = MagicMock()
    return bot


@pytest.fixture
def utility_cog(mock_bot):
    """Create a UtilityCog instance for testing."""
    return UtilityCog(mock_bot)


@pytest.fixture
def mock_interaction():
    """Create a mock interaction for testing commands."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.roles = []
    return interaction


@pytest.mark.asyncio
async def test_status_command(utility_cog, mock_interaction):
    """Test status command with complete information."""
    # Mock config values
    utility_cog.bot.config.get.side_effect = lambda section, key, default=None: {
        ConfigKeys.KEY_CONFIRM_TIME: "21:30",
        ConfigKeys.KEY_CONFIRM_WEEKDAY: "Thu",
        ConfigKeys.KEY_ANNOUNCE_TIME: "21:30",
        ConfigKeys.KEY_ANNOUNCE_WEEKDAY: "Sun",
    }.get(key, default)

    # Mock next announcement type
    utility_cog.bot.next_announcement_type = MagicMock()
    utility_cog.bot.next_announcement_type.__str__.return_value = "通常開催"  # type: ignore

    # Mock LT info
    lt_info = MagicMock()
    lt_info.speaker_name = "Test Speaker"
    lt_info.title = "Test Title"
    lt_info.url = "https://test.com"
    lt_info.is_complete = True
    utility_cog.bot.announcement_service.lt_info = lt_info

    # 日付計算の問題を修正
    with patch("bot.commands.utility_cog.datetime") as mock_datetime:
        # 固定の日付と時間を設定
        mock_today = datetime.date(2023, 1, 2)  # 月曜日
        mock_now = datetime.datetime(2023, 1, 2, 12, 0)

        # 日付オブジェクトを直接返すように設定
        mock_datetime.date.today.return_value = mock_today
        mock_datetime.datetime.now.return_value = mock_now

        # timedelataを実際のオブジェクトに
        mock_datetime.timedelta.side_effect = datetime.timedelta

        # 曜日変換をモック
        mock_datetime.date = datetime.date

        # Weekdayの定数も必要
        with patch("bot.commands.utility_cog.Weekday") as mock_weekday:
            mock_weekday.to_int.side_effect = lambda day: {"Thu": 3, "Sun": 6}.get(
                day, 0
            )
            mock_weekday.to_jp.side_effect = lambda day: {
                0: "月",
                3: "木",
                6: "日",
            }.get(day, "月")

            # Call command callback
            await utility_cog.status.callback(utility_cog, mock_interaction)

            # Verify response sent
            assert mock_interaction.response.send_message.called


@pytest.mark.asyncio
async def test_help_command_general(utility_cog, mock_interaction):
    """Test help command with no specific command."""
    # Call command callback
    await utility_cog.help_command.callback(utility_cog, mock_interaction, None)

    # Verify response contains command categories
    call_args = mock_interaction.response.send_message.call_args[0][0]
    assert "DiscordアナウンスBot - コマンドヘルプ" in call_args
    assert "LT管理コマンド:" in call_args
    assert "設定コマンド:" in call_args
    assert "ユーティリティコマンド:" in call_args
    assert "テストコマンド:" in call_args
    assert "手動実行コマンド:" in call_args


@pytest.mark.asyncio
async def test_help_command_specific(utility_cog, mock_interaction):
    """Test help command with specific command."""
    # Call command callback for LT help
    await utility_cog.help_command.callback(utility_cog, mock_interaction, "lt")

    # Verify response contains LT command details
    call_args = mock_interaction.response.send_message.call_args[0][0]
    assert "LT管理コマンド" in call_args
    assert "`/lt speaker [name]`" in call_args
    assert "`/lt title [title]`" in call_args
    assert "`/lt url [url]`" in call_args
    assert "`/lt info`" in call_args
    assert "`/lt clear`" in call_args


@pytest.mark.asyncio
async def test_test_announce_no_permission(utility_cog, mock_interaction):
    """Test test announce command without permission."""
    # Set up no permission
    with patch.object(utility_cog, "_check_admin_permissions", return_value=False):
        # Call command callback
        await utility_cog.test_announce.callback(
            utility_cog, mock_interaction, "regular"
        )

        # Verify response
        mock_interaction.response.send_message.assert_called_with(
            "このコマンドを実行する権限がありません。", ephemeral=True
        )


@pytest.mark.asyncio
async def test_test_announce_with_permission(utility_cog, mock_interaction):
    """Test test announce command with permission."""
    # Set up with permission
    with patch.object(utility_cog, "_check_admin_permissions", return_value=True):
        # Mock announcement service
        utility_cog.bot.announcement_service.generate_announcement_content.return_value = "テストメッセージ内容"

        # Call command callback
        await utility_cog.test_announce.callback(
            utility_cog, mock_interaction, "regular"
        )

        # Verify service called
        utility_cog.bot.announcement_service.generate_announcement_content.assert_called()

        # Verify response
        mock_interaction.response.send_message.assert_called_with(
            "**告知メッセージプレビュー (regular):**\n\nテストメッセージ内容",
            ephemeral=True,
        )


@pytest.mark.asyncio
async def test_test_confirm(utility_cog, mock_interaction):
    """Test test confirm command."""
    # Set up with permission
    with patch.object(utility_cog, "_check_admin_permissions", return_value=True):
        # Mock config and service
        utility_cog.bot.config.get.side_effect = lambda section, key, default=None: (
            "$role 今度の日曜 ($month/$day) の予定を確認します。"
            if key == ConfigKeys.KEY_TEMPLATE_CONFIRMATION
            else "Sun"
            if key == ConfigKeys.KEY_ANNOUNCE_WEEKDAY
            else default
        )

        # Mock get_next_weekday
        next_date = datetime.date(2023, 1, 8)  # A Sunday
        utility_cog.bot.announcement_service.get_next_weekday.return_value = next_date

        # Call command callback
        await utility_cog.test_confirm.callback(utility_cog, mock_interaction)

        # Verify response contains expected content
        call_args = mock_interaction.response.send_message.call_args[0][0]
        assert "確認メッセージプレビュー" in call_args
        assert "@Role" in call_args
        assert "1/8" in call_args  # Month/day from mocked date
        assert "👍: 通常開催" in call_args
        assert "⚡: LT開催" in call_args
        assert "💤: おやすみ" in call_args
