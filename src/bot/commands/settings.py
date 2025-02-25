"""Command handlers for bot configuration.

This module implements the command handlers for setting and getting bot
configuration options.
"""

import logging
import re
from datetime import time

import discord

from bot.config.settings import BotSettings, SettingsManager

logger = logging.getLogger(__name__)


class SettingsCommands:
    """Command handlers for bot configuration.

    Provides methods for handling commands related to bot settings.
    """

    # Valid weekday names
    VALID_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, settings: BotSettings, settings_manager: SettingsManager):
        """Initialize the settings command handlers.

        Args:
            settings: The bot settings to update.
            settings_manager: The settings manager for saving settings.
        """
        self.settings = settings
        self.settings_manager = settings_manager

    @staticmethod
    def _parse_time(time_str: str) -> time | None:
        """Parse a time string in HH:MM format.

        Args:
            time_str: The time string to parse.

        Returns:
            A time object if parsing was successful, None otherwise.
        """
        time_pattern = re.compile(r"^([0-1][0-9]|2[0-3]):([0-5][0-9])$")
        match = time_pattern.match(time_str)

        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            return time(hour, minute)

        return None

    async def handle_confirm_time(self, message: discord.Message, args: str) -> None:
        """Handle the confirm-time command.

        Sets or gets the confirmation message time.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (time in HH:MM format).
        """
        if args:
            # Set confirm time
            time_obj = self._parse_time(args.strip())
            if not time_obj:
                await message.channel.send(
                    "無効な時間形式です。HH:MM形式で入力してください。"
                )
                return

            self.settings.confirm_time = time_obj
            self.settings_manager.save()
            logger.info(f"Set confirm time to: {time_obj.strftime('%H:%M')}")
            await message.channel.send(
                f"確認メッセージ時刻を{time_obj.strftime('%H:%M')}に設定しました。"
            )
        else:
            # Get confirm time
            await message.channel.send(
                f"現在の確認メッセージ時刻: {self.settings.confirm_time.strftime('%H:%M')}"
            )

    async def handle_announce_time(self, message: discord.Message, args: str) -> None:
        """Handle the announce-time command.

        Sets or gets the announcement message time.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (time in HH:MM format).
        """
        if args:
            # Set announce time
            time_obj = self._parse_time(args.strip())
            if not time_obj:
                await message.channel.send(
                    "無効な時間形式です。HH:MM形式で入力してください。"
                )
                return

            self.settings.announce_time = time_obj
            self.settings_manager.save()
            logger.info(f"Set announce time to: {time_obj.strftime('%H:%M')}")
            await message.channel.send(
                f"告知メッセージ時刻を{time_obj.strftime('%H:%M')}に設定しました。"
            )
        else:
            # Get announce time
            await message.channel.send(
                f"現在の告知メッセージ時刻: {self.settings.announce_time.strftime('%H:%M')}"
            )

    async def handle_action_role(self, message: discord.Message, args: str) -> None:
        """Handle the action-role command.

        Sets or gets the action role.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (role mention or name).
        """
        if args:
            # Set action role
            self.settings.action_role = args.strip()
            self.settings_manager.save()
            logger.info(f"Set action role to: {self.settings.action_role}")
            await message.channel.send(
                f"アクションロールを{self.settings.action_role}に設定しました。"
            )
        else:
            # Get action role
            await message.channel.send(
                f"現在のアクションロール: {self.settings.action_role}"
            )

    async def handle_confirm_weekday(self, message: discord.Message, args: str) -> None:
        """Handle the confirm-weekday command.

        Sets or gets the confirmation message weekday.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (weekday name).
        """
        if args:
            # Set confirm weekday
            weekday = args.strip()
            if weekday not in self.VALID_WEEKDAYS:
                await message.channel.send(
                    f"無効な曜日です。有効な曜日: {', '.join(self.VALID_WEEKDAYS)}"
                )
                return

            self.settings.confirm_weekday = weekday
            self.settings_manager.save()
            logger.info(f"Set confirm weekday to: {weekday}")
            await message.channel.send(f"確認メッセージ曜日を{weekday}に設定しました。")
        else:
            # Get confirm weekday
            await message.channel.send(
                f"現在の確認メッセージ曜日: {self.settings.confirm_weekday}"
            )

    async def handle_announce_weekday(
        self, message: discord.Message, args: str
    ) -> None:
        """Handle the announce-weekday command.

        Sets or gets the announcement message weekday.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (weekday name).
        """
        if args:
            # Set announce weekday
            weekday = args.strip()
            if weekday not in self.VALID_WEEKDAYS:
                await message.channel.send(
                    f"無効な曜日です。有効な曜日: {', '.join(self.VALID_WEEKDAYS)}"
                )
                return

            self.settings.announce_weekday = weekday
            self.settings_manager.save()
            logger.info(f"Set announce weekday to: {weekday}")
            await message.channel.send(f"告知メッセージ曜日を{weekday}に設定しました。")
        else:
            # Get announce weekday
            await message.channel.send(
                f"現在の告知メッセージ曜日: {self.settings.announce_weekday}"
            )

    async def handle_default_url(self, message: discord.Message, args: str) -> None:
        """Handle the default-url command.

        Sets or gets the default URL.

        Args:
            message: The Discord message containing the command.
            args: The command arguments (URL).
        """
        if args:
            # Set default URL
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

            self.settings.default_url = url
            self.settings_manager.save()
            logger.info(f"Set default URL to: {url}")
            await message.channel.send(f"デフォルトURLを{url}に設定しました。")
        else:
            # Get default URL
            await message.channel.send(
                f"現在のデフォルトURL: {self.settings.default_url}"
            )

    async def handle_channel_setting(
        self, message: discord.Message, channel_type: str, args: str
    ) -> None:
        """Handle channel setting commands.

        Sets or gets a channel ID setting.

        Args:
            message: The Discord message containing the command.
            channel_type: The type of channel ("action", "announce", or "command").
            args: The command arguments (channel mention or ID).
        """
        attribute_name = f"{channel_type}_channel_id"

        if args:
            # Set channel ID
            # Try to extract channel ID from mention or direct ID
            channel_id = None
            mention_match = re.match(r"<#(\d+)>", args.strip())
            if mention_match:
                channel_id = int(mention_match.group(1))
            else:
                try:
                    channel_id = int(args.strip())
                except ValueError:
                    pass

            if channel_id is None:
                await message.channel.send(
                    "無効なチャンネル指定です。チャンネルをメンションするか、IDを入力してください。"
                )
                return

            # Verify channel exists
            if message.guild is None:
                return
            channel = message.guild.get_channel(channel_id)
            if not channel:
                await message.channel.send("指定されたチャンネルが見つかりません。")
                return

            setattr(self.settings, attribute_name, channel_id)
            self.settings_manager.save()
            logger.info(f"Set {channel_type} channel to: {channel.name} ({channel_id})")
            await message.channel.send(
                f"{channel_type}チャンネルを{channel.mention}に設定しました。"
            )
        else:
            # Get channel ID
            channel_id = getattr(self.settings, attribute_name)
            if channel_id:
                if message.guild is None:
                    return
                channel = message.guild.get_channel(channel_id)
                if channel:
                    await message.channel.send(
                        f"現在の{channel_type}チャンネル: {channel.mention}"
                    )
                else:
                    await message.channel.send(
                        f"現在の{channel_type}チャンネルID: {channel_id} (チャンネルが見つかりません)"
                    )
            else:
                await message.channel.send(
                    f"{channel_type}チャンネルは設定されていません。"
                )
