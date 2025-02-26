# tests/commands/test_lt_cog.py
"""Tests for the LT commands module."""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from bot.client import AnnounceBotClient
from bot.commands.lt_cog import LtCog


@pytest.fixture
def mock_bot():
    """Create a mock bot client for testing."""
    bot = MagicMock(spec=AnnounceBotClient)
    bot.announcement_service = MagicMock()
    bot.config = MagicMock()
    return bot


@pytest.fixture
def lt_cog(mock_bot):
    """Create an LtCog instance for testing."""
    return LtCog(mock_bot)


@pytest.fixture
def mock_interaction():
    """Create a mock interaction for testing commands."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.user = MagicMock(spec=discord.Member)
    interaction.user.roles = []
    return interaction


def test_lt_cog_init(mock_bot):
    """Test LtCog initialization."""
    cog = LtCog(mock_bot)
    assert cog.bot == mock_bot


def test_check_lt_admin_permissions_no_permission(lt_cog, mock_interaction):
    """Test permission check when user has no permissions."""
    # ロールを正しくセットアップ
    role = MagicMock(spec=discord.Role)
    role.name = "Regular"
    mock_interaction.user.roles = [role]

    # 設定をセットアップ
    lt_cog.bot.config.get.return_value = ["Administrator", "Moderator", "LT管理者"]

    # 権限チェック
    result = lt_cog._check_lt_admin_permissions(mock_interaction)
    assert result is False


def test_check_lt_admin_permissions_has_permission(lt_cog, mock_interaction):
    """Test permission check when user has permissions."""
    # ロールを正しくセットアップ
    role1 = MagicMock(spec=discord.Role)
    role1.name = "Regular"
    role2 = MagicMock(spec=discord.Role)
    role2.name = "LT管理者"
    mock_interaction.user.roles = [role1, role2]

    # 設定をセットアップ
    lt_cog.bot.config.get.return_value = ["Administrator", "Moderator", "LT管理者"]

    # 権限チェック
    result = lt_cog._check_lt_admin_permissions(mock_interaction)
    assert result is True


@pytest.mark.asyncio
async def test_lt_speaker_get(lt_cog, mock_interaction):
    """Test getting the speaker name."""
    # モックをセットアップ
    lt_cog.bot.announcement_service.lt_speaker = "Test Speaker"

    # コマンドのコールバック関数にアクセス
    callback = lt_cog.lt_speaker.callback

    # コールバックを直接呼び出す
    await callback(lt_cog, mock_interaction, None)

    # レスポンスを検証
    mock_interaction.response.send_message.assert_called_with(
        "現在の発表者: Test Speaker", ephemeral=True
    )


@pytest.mark.asyncio
async def test_lt_speaker_set_no_permission(lt_cog, mock_interaction):
    """Test setting speaker name without permission."""
    # 権限なしでセットアップ
    with patch.object(lt_cog, "_check_lt_admin_permissions", return_value=False):
        # コールバックにアクセス
        callback = lt_cog.lt_speaker.callback

        # コールバックを呼び出す
        await callback(lt_cog, mock_interaction, "New Speaker")

        # レスポンスを検証
        mock_interaction.response.send_message.assert_called_with(
            "LT情報を設定する権限がありません。", ephemeral=True
        )


@pytest.mark.asyncio
async def test_lt_speaker_set_with_permission(lt_cog, mock_interaction):
    """Test setting speaker name with permission."""
    # 権限ありでセットアップ
    with patch.object(lt_cog, "_check_lt_admin_permissions", return_value=True):
        # コールバックにアクセス
        callback = lt_cog.lt_speaker.callback

        # コールバックを呼び出す
        await callback(lt_cog, mock_interaction, "New Speaker")

        # レスポンスを検証
        mock_interaction.response.send_message.assert_called_with(
            "発表者を 'New Speaker' に設定しました。", ephemeral=True
        )


@pytest.mark.asyncio
async def test_lt_info(lt_cog, mock_interaction):
    """Test displaying LT info."""
    # LT情報をセットアップ
    lt_info = MagicMock()
    lt_info.speaker_name = "Test Speaker"
    lt_info.title = "Test Title"
    lt_info.url = "https://test.com"
    lt_info.is_complete = True
    lt_cog.bot.announcement_service.lt_info = lt_info

    # コールバックにアクセス
    callback = lt_cog.lt_info.callback

    # コールバックを呼び出す
    await callback(lt_cog, mock_interaction)

    # レスポンス呼び出しを検証
    assert mock_interaction.response.send_message.called


@pytest.mark.asyncio
async def test_lt_clear_no_permission(lt_cog, mock_interaction):
    """Test clearing LT info without permission."""
    # 権限なしでセットアップ
    with patch.object(lt_cog, "_check_lt_admin_permissions", return_value=False):
        # コールバックにアクセス
        callback = lt_cog.lt_clear.callback

        # コールバックを呼び出す
        await callback(lt_cog, mock_interaction)

        # レスポンスを検証
        mock_interaction.response.send_message.assert_called_with(
            "LT情報をクリアする権限がありません。", ephemeral=True
        )


@pytest.mark.asyncio
async def test_lt_clear_with_permission(lt_cog, mock_interaction):
    """Test clearing LT info with permission."""
    # 権限ありでセットアップ
    with patch.object(lt_cog, "_check_lt_admin_permissions", return_value=True):
        # コールバックにアクセス
        callback = lt_cog.lt_clear.callback

        # コールバックを呼び出す
        await callback(lt_cog, mock_interaction)

        # クリア呼び出しを検証
        assert lt_cog.bot.announcement_service.lt_info.clear.called

        # レスポンスを検証
        mock_interaction.response.send_message.assert_called_with(
            "LT情報をクリアしました。", ephemeral=True
        )
