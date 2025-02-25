"""Job definitions for the scheduler.

This module defines the jobs that are executed by the scheduler,
including sending confirmation and announcement messages.
"""

import logging

from bot.announcement.sender import AnnouncementSender
from bot.config.settings import BotSettings, SettingsManager

logger = logging.getLogger(__name__)


class ScheduledJobs:
    """Container for scheduled job functions.

    Provides methods that can be scheduled to run at specific times.
    """

    @staticmethod
    async def confirmation_job(
        sender: AnnouncementSender,
        settings: BotSettings,
        settings_manager: SettingsManager,
    ) -> None:
        """Job for sending a confirmation message.

        Args:
            sender: The announcement sender to use.
            settings: The bot settings.
            settings_manager: The settings manager for saving settings.
        """
        logger.info("Running confirmation job")
        await sender.send_confirmation_message()

    @staticmethod
    async def announcement_job(
        sender: AnnouncementSender,
        settings: BotSettings,
        settings_manager: SettingsManager,
    ) -> None:
        """Job for sending an announcement message.

        Args:
            sender: The announcement sender to use.
            settings: The bot settings.
            settings_manager: The settings manager for saving settings.
        """
        logger.info("Running announcement job")
        success = await sender.send_announcement()

        # Save settings after announcement to persist any changes
        if success:
            settings_manager.save()
