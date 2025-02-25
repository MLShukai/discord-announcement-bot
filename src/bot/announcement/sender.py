"""Message sender for Discord announcements.

This module handles the sending of announcement messages to Discord
channels.
"""

import datetime
import logging

import discord
from discord.abc import Messageable

from bot.announcement.templates import AnnouncementTemplates
from bot.config.settings import BotSettings, EventType

logger = logging.getLogger(__name__)


class AnnouncementSender:
    """Sender for Discord announcement messages.

    Handles the creation and sending of announcement messages based on
    the current event type and settings.
    """

    def __init__(self, client: discord.Client, settings: BotSettings):
        """Initialize the announcement sender.

        Args:
            client: The Discord client to use for sending messages.
            settings: The bot settings containing channel IDs and other configuration.
        """
        self.client = client
        self.settings = settings

    async def send_confirmation_message(self) -> discord.Message | None:
        """Send a confirmation message to the action channel.

        The confirmation message mentions the action role and asks for
        a reaction to determine the next event type.

        Returns:
            The sent message if successful, None otherwise.
        """
        if not self.settings.action_channel_id:
            logger.error("Action channel ID not set")
            return None

        channel = self.client.get_channel(self.settings.action_channel_id)
        if not channel or not hasattr(channel, "send"):
            logger.error(
                f"Could not find valid channel with ID {self.settings.action_channel_id}"
            )
            return None

        # Get next Sunday's date for the announcement
        today = datetime.date.today()
        days_until_sunday = (6 - today.weekday()) % 7
        next_sunday = today + datetime.timedelta(days=days_until_sunday)

        message = (
            f"{self.settings.action_role} 今度の日曜 ({next_sunday.month}/{next_sunday.day}) の予定を確認します。\n"
            "👍: 通常開催\n"
            "⚡: LT開催\n"
            "💤: おやすみ\n"
            "リアクションがない場合は通常開催として扱います。"
        )

        assert isinstance(channel, Messageable), "Channel is not messageable"

        try:
            sent_message = await channel.send(message)
            await sent_message.add_reaction("👍")
            await sent_message.add_reaction("⚡")
            await sent_message.add_reaction("💤")
            logger.info(f"Sent confirmation message: {message}")
            return sent_message
        except discord.DiscordException as e:
            logger.error(f"Failed to send confirmation message: {e}")
            return None

    async def send_announcement(self) -> bool:
        """Send an announcement message to the announcement channel.

        Creates and sends a message based on the current event type and settings.

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        if not self.settings.announce_channel_id:
            logger.error("Announcement channel ID not set")
            return False

        channel = self.client.get_channel(self.settings.announce_channel_id)
        if not channel:
            logger.error(
                f"Could not find channel with ID {self.settings.announce_channel_id}"
            )
            return False

        # Get today's date for the announcement
        today = datetime.date.today()

        # Format the message based on the event type
        if self.settings.next_event_type == EventType.REGULAR:
            message = AnnouncementTemplates.format_regular(
                today, self.settings.default_url
            )
        elif self.settings.next_event_type == EventType.LIGHTNING_TALK:
            if not self.settings.lt_info.is_complete():
                logger.error("Lightning Talk information is incomplete")
                return False

            message = AnnouncementTemplates.format_lightning_talk(
                today,
                self.settings.lt_info.speaker,
                self.settings.lt_info.title,
                self.settings.lt_info.url or self.settings.default_url,
            )
        else:  # EventType.REST
            message = AnnouncementTemplates.format_rest()

        assert isinstance(channel, Messageable), "Channel is not messageable"

        try:
            await channel.send(message)
            logger.info(f"Sent announcement: {message}")

            # Clear LT info after announcement
            if self.settings.next_event_type == EventType.LIGHTNING_TALK:
                self.settings.lt_info.clear()

            # Reset to default event type
            self.settings.next_event_type = EventType.REGULAR

            return True
        except discord.DiscordException as e:
            logger.error(f"Failed to send announcement: {e}")
            return False

    @staticmethod
    async def process_confirmation_reaction(
        reaction: discord.Reaction, settings: BotSettings
    ) -> None:
        """Process a reaction to the confirmation message.

        Updates the next event type based on the reaction emoji.

        Args:
            reaction: The reaction to process.
            settings: The bot settings to update.
        """
        emoji = str(reaction.emoji)

        if emoji == "👍":
            settings.next_event_type = EventType.REGULAR
            logger.info("Next event set to REGULAR")
        elif emoji == "⚡":
            settings.next_event_type = EventType.LIGHTNING_TALK
            logger.info("Next event set to LIGHTNING_TALK")
        elif emoji == "💤":
            settings.next_event_type = EventType.REST
            logger.info("Next event set to REST")
