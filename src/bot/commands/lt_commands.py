"""Command handlers for Lightning Talk configuration.

This module implements slash commands for setting and getting Lightning
Talk information.
"""

import logging
import re

import discord
from discord import app_commands
from discord.ext import commands

from bot.config.settings import BotSettings, SettingsManager

logger = logging.getLogger(__name__)


class LightningTalkCommands(commands.Cog):
    """Lightning Talk related commands.

    Provides commands for managing Lightning Talk information such as
    speaker, title, and URL.
    """

    lt_group = app_commands.Group(
        name="lt", description="Lightning Talk related commands"
    )

    def __init__(
        self,
        bot: commands.Bot,
        settings: BotSettings,
        settings_manager: SettingsManager,
    ):
        """Initialize the Lightning Talk command handlers.

        Args:
            bot: The Discord bot instance.
            settings: The bot settings to update.
            settings_manager: The settings manager for saving settings.
        """
        self.bot = bot
        self.settings = settings
        self.settings_manager = settings_manager

    @lt_group.command(
        name="speaker", description="Set or get the Lightning Talk speaker"
    )
    @app_commands.describe(name="The name of the speaker")
    async def lt_speaker(
        self, interaction: discord.Interaction, name: str | None = None
    ) -> None:
        """Set or get the Lightning Talk speaker name.

        Args:
            interaction: The Discord interaction.
            name: The name of the speaker (optional).
        """
        if name:
            # Set speaker name
            self.settings.lt_info.speaker = name
            logger.info(f"Set LT speaker to: {self.settings.lt_info.speaker}")
            await interaction.response.send_message(
                f"LT発表者を「{self.settings.lt_info.speaker}」に設定しました。"
            )
        else:
            # Get speaker name
            if self.settings.lt_info.speaker:
                await interaction.response.send_message(
                    f"現在のLT発表者: {self.settings.lt_info.speaker}"
                )
            else:
                await interaction.response.send_message(
                    "LT発表者はまだ設定されていません。"
                )

    @lt_group.command(name="title", description="Set or get the Lightning Talk title")
    @app_commands.describe(title="The title of the talk")
    async def lt_title(
        self, interaction: discord.Interaction, title: str | None = None
    ) -> None:
        """Set or get the Lightning Talk title.

        Args:
            interaction: The Discord interaction.
            title: The title of the talk (optional).
        """
        if title:
            # Set title
            self.settings.lt_info.title = title
            logger.info(f"Set LT title to: {self.settings.lt_info.title}")
            await interaction.response.send_message(
                f"LTタイトルを「{self.settings.lt_info.title}」に設定しました。"
            )
        else:
            # Get title
            if self.settings.lt_info.title:
                await interaction.response.send_message(
                    f"現在のLTタイトル: {self.settings.lt_info.title}"
                )
            else:
                await interaction.response.send_message(
                    "LTタイトルはまだ設定されていません。"
                )

    @lt_group.command(name="url", description="Set or get the Lightning Talk URL")
    @app_commands.describe(url="The URL for the Lightning Talk")
    async def lt_url(
        self, interaction: discord.Interaction, url: str | None = None
    ) -> None:
        """Set or get the Lightning Talk URL.

        Args:
            interaction: The Discord interaction.
            url: The URL for the talk (optional).
        """
        if url:
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
                await interaction.response.send_message(
                    "無効なURLです。有効なURLを入力してください。"
                )
                return

            # Set URL
            self.settings.lt_info.url = url
            logger.info(f"Set LT URL to: {self.settings.lt_info.url}")
            await interaction.response.send_message(
                f"LT URLを「{self.settings.lt_info.url}」に設定しました。"
            )
        else:
            # Get URL
            if self.settings.lt_info.url:
                await interaction.response.send_message(
                    f"現在のLT URL: {self.settings.lt_info.url}"
                )
            else:
                await interaction.response.send_message(
                    f"LT URLはまだ設定されていません。デフォルトURL: {self.settings.default_url}"
                )

    @lt_group.command(
        name="info", description="Display all current Lightning Talk information"
    )
    async def lt_info(self, interaction: discord.Interaction) -> None:
        """Display all current Lightning Talk information.

        Args:
            interaction: The Discord interaction.
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

        await interaction.response.send_message(info_text)

    @lt_group.command(name="clear", description="Clear all Lightning Talk information")
    async def lt_clear(self, interaction: discord.Interaction) -> None:
        """Clear all Lightning Talk information.

        Args:
            interaction: The Discord interaction.
        """
        self.settings.lt_info.clear()
        logger.info("Cleared all LT information")
        await interaction.response.send_message("LT情報をクリアしました。")
