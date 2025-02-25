"""Discord client implementation for the announcement bot.

This module implements the Discord client, including event handlers and
command processing.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import override

import discord
from discord.ext import commands

from bot.announcement.sender import AnnouncementSender
from bot.commands.lt_commands import LightningTalkCommands
from bot.commands.settings import SettingsCommands
from bot.config.settings import SettingsManager
from bot.scheduler.jobs import ScheduledJobs
from bot.scheduler.scheduler import JobScheduler

logger = logging.getLogger(__name__)


class AnnouncementBot(commands.Bot):
    """Discord bot for making announcements.

    Handles Discord events, command processing, and interactions with
    the scheduler and other components.
    """

    def __init__(self, settings_manager: SettingsManager):
        """Initialize the announcement bot.

        Args:
            settings_manager: The settings manager for loading and saving settings.
        """
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True

        super().__init__(command_prefix="/bot ", intents=intents)

        self.settings_manager = settings_manager
        self.settings = settings_manager.load()

        self.lt_commands = LightningTalkCommands(self.settings, self.settings_manager)
        self.settings_commands = SettingsCommands(self.settings, self.settings_manager)

        # Will be initialized in on_ready
        self.sender = None
        self.scheduler = None
        self.confirmation_message_id = None

        # Command handlers mapping
        self.command_handlers: dict[
            str, Callable[[discord.Message, str], Awaitable[None]]
        ] = {
            # LT commands
            "lt-speaker": self.lt_commands.handle_lt_speaker,
            "lt-title": self.lt_commands.handle_lt_title,
            "lt-url": self.lt_commands.handle_lt_url,
            "lt-info": lambda msg, _: self.lt_commands.handle_lt_info(msg),
            "lt-clear": lambda msg, _: self.lt_commands.handle_lt_clear(msg),
            # Settings commands
            "confirm-time": self.settings_commands.handle_confirm_time,
            "announce-time": self.settings_commands.handle_announce_time,
            "action-role": self.settings_commands.handle_action_role,
            "confirm-weekday": self.settings_commands.handle_confirm_weekday,
            "announce-weekday": self.settings_commands.handle_announce_weekday,
            "default-url": self.settings_commands.handle_default_url,
            # Channel settings
            "action-channel": lambda msg,
            args: self.settings_commands.handle_channel_setting(msg, "action", args),
            "announce-channel": lambda msg,
            args: self.settings_commands.handle_channel_setting(msg, "announce", args),
            "command-channel": lambda msg,
            args: self.settings_commands.handle_channel_setting(msg, "command", args),
            # Other commands
            "help": self.handle_help,
            "status": self.handle_status,
        }

    async def on_ready(self) -> None:
        """Handle the bot ready event.

        Sets up the announcement sender and scheduler when the bot
        connects to Discord.
        """
        if self.user is not None:
            logger.info(f"Bot connected as {self.user.name} ({self.user.id})")

        # Initialize sender and scheduler
        self.sender = AnnouncementSender(self, self.settings)
        self.scheduler = JobScheduler(self.settings)

        # Set up scheduled jobs
        self.scheduler.add_confirmation_job(
            ScheduledJobs.confirmation_job,
            self.sender,
            self.settings,
            self.settings_manager,
        )

        self.scheduler.add_announcement_job(
            ScheduledJobs.announcement_job,
            self.sender,
            self.settings,
            self.settings_manager,
        )

        # Start the scheduler
        self.scheduler.start()

        logger.info("Bot is now ready")

    @override
    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages.

        Processes commands and handles errors.

        Args:
            message: The Discord message to process.
        """
        # Ignore messages from bots, including self
        if message.author.bot:
            return

        # Check if this is a command
        if message.content.startswith("/bot "):
            # Check if command channel is set and this is not it
            if (
                self.settings.command_channel_id
                and message.channel.id != self.settings.command_channel_id
            ):
                return

            await self._process_command(message)

        # Let the command framework process commands too
        await self.process_commands(message)

    async def on_reaction_add(
        self, reaction: discord.Reaction, user: discord.User
    ) -> None:
        """Handle reaction added event.

        Processes reactions to confirmation messages to set the next event type.

        Args:
            reaction: The reaction that was added.
            user: The user who added the reaction.
        """
        # Ignore reactions from bots, including self
        if user.bot:
            return

        # Check if this is a reaction to the confirmation message
        if (
            self.confirmation_message_id
            and reaction.message.id == self.confirmation_message_id
        ):
            await AnnouncementSender.process_confirmation_reaction(
                reaction, self.settings
            )
            self.settings_manager.save()

    async def _process_command(self, message: discord.Message) -> None:
        """Process a bot command.

        Parses the command and arguments, then calls the appropriate handler.

        Args:
            message: The Discord message containing the command.
        """
        # Parse command and arguments
        try:
            # Remove prefix
            content = message.content[5:].strip()

            # Split into command and arguments
            parts = content.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            # Find and call handler
            handler = self.command_handlers.get(command)
            if handler:
                try:
                    await handler(message, args)
                except Exception as e:
                    logger.error(f"Error handling command '{command}': {e}")
                    await message.channel.send(
                        f"コマンド '{command}' の処理中にエラーが発生しました: {e}"
                    )
            else:
                await message.channel.send(
                    f"不明なコマンド '{command}' です。`/bot help` でコマンド一覧を確認できます。"
                )
        except Exception as e:
            logger.error(f"Error parsing command: {e}")
            await message.channel.send(f"コマンドの解析中にエラーが発生しました: {e}")

    async def handle_help(self, message: discord.Message, args: str) -> None:
        """Handle the help command.

        Displays a list of available commands.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (unused).
        """
        help_text = """
**Discord 告知Bot コマンド一覧**

**LT情報設定:**
`/bot lt-speaker <name>` - LT発表者を設定
`/bot lt-title <title>` - LTタイトルを設定
`/bot lt-url <url>` - LT URLを設定
`/bot lt-info` - 現在のLT情報を表示
`/bot lt-clear` - LT情報をクリア

**時間設定:**
`/bot confirm-time <HH:MM>` - 確認メッセージ時刻を設定
`/bot announce-time <HH:MM>` - 告知メッセージ時刻を設定

**曜日設定:**
`/bot confirm-weekday <Mon, Tue, ...>` - 確認メッセージ曜日を設定
`/bot announce-weekday <Mon, Tue, ...>` - 告知メッセージ曜日を設定

**その他設定:**
`/bot action-role <@role or name>` - アクションロールを設定
`/bot default-url <url>` - デフォルトURLを設定
`/bot action-channel <#channel or id>` - アクションチャンネルを設定
`/bot announce-channel <#channel or id>` - 告知チャンネルを設定
`/bot command-channel <#channel or id>` - コマンドチャンネルを設定

**その他コマンド:**
`/bot status` - 現在の設定状態を表示
`/bot help` - このヘルプを表示

いずれのコマンドも、引数なしで実行すると現在の設定値を表示します。
"""
        await message.channel.send(help_text)

    async def handle_status(self, message: discord.Message, args: str) -> None:
        """Handle the status command.

        Displays the current bot status and settings.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (unused).
        """
        # 型チェックを追加
        action_channel = self.get_channel(self.settings.action_channel_id)
        action_channel_name = (
            getattr(action_channel, "mention", "未設定") if action_channel else "未設定"
        )

        announce_channel = self.get_channel(self.settings.announce_channel_id)
        announce_channel_name = (
            getattr(announce_channel, "mention", "未設定")
            if announce_channel
            else "未設定"
        )

        command_channel = self.get_channel(self.settings.command_channel_id)
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
        await message.channel.send(status_text)
