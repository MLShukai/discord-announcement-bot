"""Command handlers for Lightning Talk configuration.

This module implements the command handlers for setting and getting
Lightning Talk information.
"""

import logging
import re

import discord

from bot.config.settings import BotSettings, SettingsManager

logger = logging.getLogger(__name__)


class LightningTalkCommands:
    """Command handlers for Lightning Talk configuration.

    Provides methods for handling commands related to Lightning Talk
    settings.
    """

    def __init__(self, settings: BotSettings, settings_manager: SettingsManager):
        """Initialize the Lightning Talk command handlers.

        Args:
            settings: The bot settings to update.
            settings_manager: The settings manager for saving settings.
        """
        self.settings = settings
        self.settings_manager = settings_manager

    async def handle_lt_speaker(self, message: discord.Message, args: str) -> None:
        """Handle the lt-speaker command.

        Sets or gets the Lightning Talk speaker name.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (speaker name).
        """
        if args:
            # Set speaker name
            self.settings.lt_info.speaker = args.strip()
            logger.info(f"Set LT speaker to: {self.settings.lt_info.speaker}")
            await message.channel.send(
                f"LT発表者を「{self.settings.lt_info.speaker}」に設定しました。"
            )
        else:
            # Get speaker name
            if self.settings.lt_info.speaker:
                await message.channel.send(
                    f"現在のLT発表者: {self.settings.lt_info.speaker}"
                )
            else:
                await message.channel.send("LT発表者はまだ設定されていません。")

    async def handle_lt_title(self, message: discord.Message, args: str) -> None:
        """Handle the lt-title command.

        Sets or gets the Lightning Talk title.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (talk title).
        """
        if args:
            # Set title
            self.settings.lt_info.title = args.strip()
            logger.info(f"Set LT title to: {self.settings.lt_info.title}")
            await message.channel.send(
                f"LTタイトルを「{self.settings.lt_info.title}」に設定しました。"
            )
        else:
            # Get title
            if self.settings.lt_info.title:
                await message.channel.send(
                    f"現在のLTタイトル: {self.settings.lt_info.title}"
                )
            else:
                await message.channel.send("LTタイトルはまだ設定されていません。")

    async def handle_lt_url(self, message: discord.Message, args: str) -> None:
        """Handle the lt-url command.

        Sets or gets the Lightning Talk URL.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (URL).
        """
        if args:
            url = args.strip()
            # Simple URL validation
            url_pattern = re.compile(
                r"^https?://"  # http:// or https://
                r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
                r"localhost|"  # localhost
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
                r"(?::\d+)?"  # optional port
                r"(?:/?|[/?]\S+)$",
                re.IGNORECASE,
            )

            if not url_pattern.match(url):
                await message.channel.send(
                    "無効なURLです。有効なURLを入力してください。"
                )
                return

            # Set URL
            self.settings.lt_info.url = url
            logger.info(f"Set LT URL to: {self.settings.lt_info.url}")
            await message.channel.send(
                f"LT URLを「{self.settings.lt_info.url}」に設定しました。"
            )
        else:
            # Get URL
            if self.settings.lt_info.url:
                await message.channel.send(f"現在のLT URL: {self.settings.lt_info.url}")
            else:
                await message.channel.send(
                    f"LT URLはまだ設定されていません。デフォルトURL: {self.settings.default_url}"
                )

    async def handle_lt_info(self, message: discord.Message) -> None:
        """Handle the lt-info command.

        Displays all current Lightning Talk information.

        Args:
            message: The Discord message containing the command.
        """
        if self.settings.lt_info.is_complete():
            info_text = (
                "**現在のLT情報:**\n"
                f"発表者: {self.settings.lt_info.speaker}\n"
                f"タイトル: {self.settings.lt_info.title}\n"
                f"URL: {self.settings.lt_info.url or self.settings.default_url}"
            )
        else:
            missing: list[str] = []
            if not self.settings.lt_info.speaker:
                missing.append("発表者")
            if not self.settings.lt_info.title:
                missing.append("タイトル")
            if not self.settings.lt_info.url:
                missing.append("URL")

            info_text = (
                "**現在のLT情報:**\n"
                f"発表者: {self.settings.lt_info.speaker or '未設定'}\n"
                f"タイトル: {self.settings.lt_info.title or '未設定'}\n"
                f"URL: {self.settings.lt_info.url or self.settings.default_url}\n\n"
                f"**注意:** {', '.join(missing)}が設定されていません。"
            )

        await message.channel.send(info_text)

    async def handle_lt_clear(self, message: discord.Message) -> None:
        """Handle the lt-clear command.

        Clears all Lightning Talk information.

        Args:
            message: The Discord message containing the command.
        """
        self.settings.lt_info.clear()
        logger.info("Cleared all LT information")
        await message.channel.send("LT情報をクリアしました。")
