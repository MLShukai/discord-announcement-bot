"""Main command group for the announce-bot.

This module implements the root slash command and utility commands.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.config.settings import BotSettings

logger = logging.getLogger(__name__)


class BotUtilityCommands(commands.Cog):
    """Utility commands for the announcement bot."""

    announce_bot_group = app_commands.Group(
        name="announce-bot", description="Announcement bot commands"
    )

    def __init__(self, bot: commands.Bot, settings: BotSettings):
        """Initialize utility command handlers.

        Args:
            bot: Discord bot instance.
            settings: Bot settings.
        """
        self.bot = bot
        self.settings = settings

    @announce_bot_group.command(
        name="status", description="Display current bot status and settings"
    )
    async def status(self, interaction: discord.Interaction) -> None:
        """Display current bot status and settings.

        Args:
            interaction: Discord interaction.
        """
        # チャンネル情報の取得
        action_channel = self.bot.get_channel(self.settings.action_channel_id)
        action_channel_name = (
            getattr(action_channel, "mention", "未設定") if action_channel else "未設定"
        )

        announce_channel = self.bot.get_channel(self.settings.announce_channel_id)
        announce_channel_name = (
            getattr(announce_channel, "mention", "未設定")
            if announce_channel
            else "未設定"
        )

        command_channel = self.bot.get_channel(self.settings.command_channel_id)
        command_channel_name = (
            getattr(command_channel, "mention", "未設定")
            if command_channel
            else "未設定"
        )

        status_text = f"""
**Discord 告知Bot ステータス**

**時間設定:**
- 確認メッセージ時刻: {self.settings.confirm_time.strftime('%H:%M')}
- 告知メッセージ時刻: {self.settings.announce_time.strftime('%H:%M')}

**曜日設定:**
- 確認メッセージ曜日: {self.settings.confirm_weekday}
- 告知メッセージ曜日: {self.settings.announce_weekday}

**チャンネル設定:**
- アクションチャンネル: {action_channel_name}
- 告知チャンネル: {announce_channel_name}
- コマンドチャンネル: {command_channel_name}

**その他設定:**
- アクションロール: {self.settings.action_role}
- デフォルトURL: {self.settings.default_url}

**次回イベント: **{self.settings.next_event_type.name}
"""
        await interaction.response.send_message(status_text)

    @announce_bot_group.command(name="help", description="Show help information")
    async def help(self, interaction: discord.Interaction) -> None:
        """Show help information.

        Args:
            interaction: Discord interaction.
        """
        help_text = """
**Discord 告知Bot コマンド一覧**

**/announce-bot lt speaker [name]** - LT発表者を設定
**/announce-bot lt title [title]** - LTタイトルを設定
**/announce-bot lt url [url]** - LT URLを設定
**/announce-bot lt info** - 現在のLT情報を表示
**/announce-bot lt clear** - LT情報をクリア

**/announce-bot settings time confirm [HH:MM]** - 確認メッセージ時刻を設定
**/announce-bot settings time announce [HH:MM]** - 告知メッセージ時刻を設定

**/announce-bot settings weekday confirm [曜日]** - 確認メッセージ曜日を設定
**/announce-bot settings weekday announce [曜日]** - 告知メッセージ曜日を設定

**/announce-bot settings role [ロール]** - アクションロールを設定
**/announce-bot settings url [URL]** - デフォルトURLを設定

**/announce-bot settings channel action [チャンネル]** - アクションチャンネルを設定
**/announce-bot settings channel announce [チャンネル]** - 告知チャンネルを設定
**/announce-bot settings channel command [チャンネル]** - コマンドチャンネルを設定

**/announce-bot status** - 現在の設定状態を表示
**/announce-bot help** - このヘルプを表示

いずれのコマンドも、引数がない場合は現在の設定値を表示します。
"""
        await interaction.response.send_message(help_text)
