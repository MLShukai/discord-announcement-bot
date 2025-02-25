"""Discord client implementation for the announcement bot.

This module implements the Discord client, including event handlers and
command processing.
"""

import logging
from typing import override

import discord
from discord.ext import commands

from bot.announcement.sender import AnnouncementSender
from bot.commands.bot_commands import BotUtilityCommands
from bot.commands.lt_commands import LightningTalkCommands
from bot.commands.settings_commands import (
    SettingsChannelCommands,
    SettingsCommands,
    SettingsTimeCommands,
    SettingsWeekdayCommands,
)
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

        super().__init__(command_prefix="!", intents=intents)

        self.settings_manager = settings_manager
        self.settings = settings_manager.load()

        # Will be initialized in on_ready
        self.sender = None
        self.scheduler = None
        self.confirmation_message_id = None

        # Remove default help command
        self.remove_command("help")

    @override
    async def setup_hook(self) -> None:
        """Set up the bot's extensions and commands.

        This is called automatically when the bot starts.
        """
        # Initialize sender and scheduler
        self.sender = AnnouncementSender(self, self.settings)
        self.scheduler = JobScheduler(self.settings)

        # Create command handlers
        bot_commands = BotUtilityCommands(self, self.settings)
        lt_commands = LightningTalkCommands(self, self.settings, self.settings_manager)
        settings_commands = SettingsCommands(self, self.settings, self.settings_manager)
        time_commands = SettingsTimeCommands(self, self.settings, self.settings_manager)
        weekday_commands = SettingsWeekdayCommands(
            self, self.settings, self.settings_manager
        )
        channel_commands = SettingsChannelCommands(
            self, self.settings, self.settings_manager
        )

        # Add cogs
        await self.add_cog(bot_commands)
        await self.add_cog(lt_commands)
        await self.add_cog(settings_commands)
        await self.add_cog(time_commands)
        await self.add_cog(weekday_commands)
        await self.add_cog(channel_commands)

        # Add settings subgroups
        settings_commands.settings_group.add_command(time_commands.time_group)
        settings_commands.settings_group.add_command(weekday_commands.weekday_group)
        settings_commands.settings_group.add_command(channel_commands.channel_group)

        # Sync commands
        await self.tree.sync()
        logger.info("Command tree synced")

    async def on_ready(self) -> None:
        """Handle the bot ready event.

        Sets up the announcement sender and scheduler when the bot
        connects to Discord.
        """
        if self.user is not None:
            logger.info(f"Bot connected as {self.user.name} ({self.user.id})")

        if self.scheduler is not None:
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
