"""Command handlers for bot configuration.

This module implements slash commands for setting and getting bot
configuration options.
"""

import logging
import re
from datetime import time
from typing import override

import discord
from discord import app_commands
from discord.ext import commands

from bot.config.settings import BotSettings, SettingsManager

logger = logging.getLogger(__name__)


class TimeTransformer(app_commands.Transformer):
    """Transformer for handling time input in HH:MM format."""

    @override
    async def transform(self, interaction: discord.Interaction, value: str) -> time:
        """Transform string time input to time object.

        Args:
            interaction: Discord interaction.
            value: Time string in HH:MM format.

        Returns:
            Parsed time object if valid.

        Raises:
            app_commands.TransformerError: If time format is invalid.
        """
        time_pattern = re.compile(r"^([0-1][0-9]|2[0-3]):([0-5][0-9])$")
        match = time_pattern.match(value)

        if not match:
            raise ValueError("無効な時間形式です。HH:MM形式で入力してください。")

        hour = int(match.group(1))
        minute = int(match.group(2))
        return time(hour, minute)


class WeekdayTransformer(app_commands.Transformer):
    """Transformer for handling weekday input."""

    VALID_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    @override
    async def transform(self, interaction: discord.Interaction, value: str) -> str:
        """Transform weekday input string.

        Args:
            interaction: Discord interaction.
            value: Weekday string.

        Returns:
            Validated weekday string if valid.

        Raises:
            app_commands.TransformerError: If weekday is invalid.
        """
        if value not in self.VALID_WEEKDAYS:
            raise ValueError(
                f"無効な曜日です。有効な曜日: {', '.join(self.VALID_WEEKDAYS)}"
            )
        return value


class SettingsTimeCommands(commands.Cog):
    """Commands for managing time settings."""

    time_group = app_commands.Group(name="time", description="Time related settings")

    def __init__(
        self,
        bot: commands.Bot,
        settings: BotSettings,
        settings_manager: SettingsManager,
    ):
        """Initialize time settings command handlers.

        Args:
            bot: Discord bot instance.
            settings: Bot settings to update.
            settings_manager: Settings manager for saving settings.
        """
        super().__init__()
        self.bot = bot
        self.settings = settings
        self.settings_manager = settings_manager

    @time_group.command(
        name="confirm", description="Set or get confirmation message time"
    )
    @app_commands.describe(time_value="Time in HH:MM format")
    async def confirm_time(
        self,
        interaction: discord.Interaction,
        time_value: app_commands.Transform[time, TimeTransformer] | None = None,
    ) -> None:
        """Set or get confirmation message time.

        Args:
            interaction: Discord interaction.
            time_value: Time in HH:MM format (optional).
        """
        if time_value:
            # Set confirm time
            self.settings.confirm_time = time_value
            self.settings_manager.save()
            logger.info(f"Set confirm time to: {time_value.strftime('%H:%M')}")
            await interaction.response.send_message(
                f"確認メッセージ時刻を{time_value.strftime('%H:%M')}に設定しました。"
            )
        else:
            # Get confirm time
            await interaction.response.send_message(
                f"現在の確認メッセージ時刻: {self.settings.confirm_time.strftime('%H:%M')}"
            )

    @time_group.command(
        name="announce", description="Set or get announcement message time"
    )
    @app_commands.describe(time_value="Time in HH:MM format")
    async def announce_time(
        self,
        interaction: discord.Interaction,
        time_value: app_commands.Transform[time, TimeTransformer] | None = None,
    ) -> None:
        """Set or get announcement message time.

        Args:
            interaction: Discord interaction.
            time_value: Time in HH:MM format (optional).
        """
        if time_value:
            # Set announce time
            self.settings.announce_time = time_value
            self.settings_manager.save()
            logger.info(f"Set announce time to: {time_value.strftime('%H:%M')}")
            await interaction.response.send_message(
                f"告知メッセージ時刻を{time_value.strftime('%H:%M')}に設定しました。"
            )
        else:
            # Get announce time
            await interaction.response.send_message(
                f"現在の告知メッセージ時刻: {self.settings.announce_time.strftime('%H:%M')}"
            )


class SettingsWeekdayCommands(commands.Cog):
    """Commands for managing weekday settings."""

    weekday_group = app_commands.Group(
        name="weekday", description="Weekday related settings"
    )

    def __init__(
        self,
        bot: commands.Bot,
        settings: BotSettings,
        settings_manager: SettingsManager,
    ):
        """Initialize weekday settings command handlers.

        Args:
            bot: Discord bot instance.
            settings: Bot settings to update.
            settings_manager: Settings manager for saving settings.
        """
        super().__init__()
        self.bot = bot
        self.settings = settings
        self.settings_manager = settings_manager

    @weekday_group.command(
        name="confirm", description="Set or get confirmation message weekday"
    )
    @app_commands.describe(
        weekday="Day of the week (Mon, Tue, Wed, Thu, Fri, Sat, Sun)"
    )
    @app_commands.choices(
        weekday=[
            app_commands.Choice(name=day, value=day)
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ]
    )
    async def confirm_weekday(
        self, interaction: discord.Interaction, weekday: str | None = None
    ) -> None:
        """Set or get confirmation message weekday.

        Args:
            interaction: Discord interaction.
            weekday: Day of the week (optional).
        """
        if weekday:
            # Set confirm weekday
            self.settings.confirm_weekday = weekday
            self.settings_manager.save()
            logger.info(f"Set confirm weekday to: {weekday}")
            await interaction.response.send_message(
                f"確認メッセージ曜日を{weekday}に設定しました。"
            )
        else:
            # Get confirm weekday
            await interaction.response.send_message(
                f"現在の確認メッセージ曜日: {self.settings.confirm_weekday}"
            )

    @weekday_group.command(
        name="announce", description="Set or get announcement message weekday"
    )
    @app_commands.describe(
        weekday="Day of the week (Mon, Tue, Wed, Thu, Fri, Sat, Sun)"
    )
    @app_commands.choices(
        weekday=[
            app_commands.Choice(name=day, value=day)
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ]
    )
    async def announce_weekday(
        self, interaction: discord.Interaction, weekday: str | None = None
    ) -> None:
        """Set or get announcement message weekday.

        Args:
            interaction: Discord interaction.
            weekday: Day of the week (optional).
        """
        if weekday:
            # Set announce weekday
            self.settings.announce_weekday = weekday
            self.settings_manager.save()
            logger.info(f"Set announce weekday to: {weekday}")
            await interaction.response.send_message(
                f"告知メッセージ曜日を{weekday}に設定しました。"
            )
        else:
            # Get announce weekday
            await interaction.response.send_message(
                f"現在の告知メッセージ曜日: {self.settings.announce_weekday}"
            )


class SettingsChannelCommands(commands.Cog):
    """Commands for managing channel settings."""

    channel_group = app_commands.Group(
        name="channel", description="Channel related settings"
    )

    def __init__(
        self,
        bot: commands.Bot,
        settings: BotSettings,
        settings_manager: SettingsManager,
    ):
        """Initialize channel settings command handlers.

        Args:
            bot: Discord bot instance.
            settings: Bot settings to update.
            settings_manager: Settings manager for saving settings.
        """
        super().__init__()
        self.bot = bot
        self.settings = settings
        self.settings_manager = settings_manager

    @channel_group.command(name="action", description="Set or get action channel")
    @app_commands.describe(channel="The channel for confirmation actions")
    async def action_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Set or get action channel.

        Args:
            interaction: Discord interaction.
            channel: Text channel for actions (optional).
        """
        if channel:
            self.settings.action_channel_id = channel.id
            self.settings_manager.save()
            logger.info(f"Set action channel to: {channel.name} ({channel.id})")
            await interaction.response.send_message(
                f"アクションチャンネルを{channel.mention}に設定しました。"
            )
        else:
            if self.settings.action_channel_id:
                ch = self.bot.get_channel(self.settings.action_channel_id)
                if ch:
                    await interaction.response.send_message(
                        f"現在のアクションチャンネル: {ch.mention}"  # type: ignore
                    )
                else:
                    await interaction.response.send_message(
                        f"現在のアクションチャンネルID: {self.settings.action_channel_id} "
                        "(チャンネルが見つかりません)"
                    )
            else:
                await interaction.response.send_message(
                    "アクションチャンネルは設定されていません。"
                )

    @channel_group.command(
        name="announce", description="Set or get announcement channel"
    )
    @app_commands.describe(channel="The channel for announcements")
    async def announce_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Set or get announcement channel.

        Args:
            interaction: Discord interaction.
            channel: Text channel for announcements (optional).
        """
        if channel:
            self.settings.announce_channel_id = channel.id
            self.settings_manager.save()
            logger.info(f"Set announce channel to: {channel.name} ({channel.id})")
            await interaction.response.send_message(
                f"告知チャンネルを{channel.mention}に設定しました。"
            )
        else:
            if self.settings.announce_channel_id:
                channel = self.bot.get_channel(self.settings.announce_channel_id)  # type: ignore
                if channel:
                    await interaction.response.send_message(
                        f"現在の告知チャンネル: {channel.mention}"
                    )
                else:
                    await interaction.response.send_message(
                        f"現在の告知チャンネルID: {self.settings.announce_channel_id} "
                        "(チャンネルが見つかりません)"
                    )
            else:
                await interaction.response.send_message(
                    "告知チャンネルは設定されていません。"
                )

    @channel_group.command(name="command", description="Set or get command channel")
    @app_commands.describe(channel="The channel for bot commands")
    async def command_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Set or get command channel.

        Args:
            interaction: Discord interaction.
            channel: Text channel for commands (optional).
        """
        if channel:
            self.settings.command_channel_id = channel.id
            self.settings_manager.save()
            logger.info(f"Set command channel to: {channel.name} ({channel.id})")
            await interaction.response.send_message(
                f"コマンドチャンネルを{channel.mention}に設定しました。"
            )
        else:
            if self.settings.command_channel_id:
                ch = self.bot.get_channel(self.settings.command_channel_id)
                if ch:
                    await interaction.response.send_message(
                        f"現在のコマンドチャンネル: {ch.mention}"  # type: ignore
                    )
                else:
                    await interaction.response.send_message(
                        f"現在のコマンドチャンネルID: {self.settings.command_channel_id} "
                        "(チャンネルが見つかりません)"
                    )
            else:
                await interaction.response.send_message(
                    "コマンドチャンネルは設定されていません。"
                )


class SettingsCommands(commands.Cog):
    """Commands for managing bot settings."""

    settings_group = app_commands.Group(
        name="settings", description="Bot settings commands"
    )

    def __init__(
        self,
        bot: commands.Bot,
        settings: BotSettings,
        settings_manager: SettingsManager,
    ):
        """Initialize settings command handlers.

        Args:
            bot: Discord bot instance.
            settings: Bot settings to update.
            settings_manager: Settings manager for saving settings.
        """
        self.bot = bot
        self.settings = settings
        self.settings_manager = settings_manager

    @settings_group.command(name="role", description="Set or get action role")
    @app_commands.describe(role="The role to mention for actions")
    async def action_role(
        self, interaction: discord.Interaction, role: discord.Role | None = None
    ) -> None:
        """Set or get action role.

        Args:
            interaction: Discord interaction.
            role: Role to mention (optional).
        """
        if role:
            self.settings.action_role = role.mention
            self.settings_manager.save()
            logger.info(f"Set action role to: {self.settings.action_role}")
            await interaction.response.send_message(
                f"アクションロールを{self.settings.action_role}に設定しました。"
            )
        else:
            await interaction.response.send_message(
                f"現在のアクションロール: {self.settings.action_role}"
            )

    @settings_group.command(name="url", description="Set or get default URL")
    @app_commands.describe(url="The default URL for announcements")
    async def default_url(
        self, interaction: discord.Interaction, url: str | None = None
    ) -> None:
        """Set or get default URL.

        Args:
            interaction: Discord interaction.
            url: Default URL for announcements (optional).
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

            self.settings.default_url = url
            self.settings_manager.save()
            logger.info(f"Set default URL to: {url}")
            await interaction.response.send_message(
                f"デフォルトURLを{url}に設定しました。"
            )
        else:
            await interaction.response.send_message(
                f"現在のデフォルトURL: {self.settings.default_url}"
            )
