"""Entry point for the Discord announcement bot.

This module sets up logging and starts the bot.
"""

import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import discord
import dotenv

from bot.client import AnnouncementBot
from bot.config.settings import SettingsManager


def setup_logging(log_dir: str | None = None) -> None:
    """Set up logging configuration.

    Args:
        log_dir: Directory to store log files. If None, logs to console only.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if log directory is specified
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path / "bot.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


async def main() -> None:
    """Start the bot.

    Loads environment variables, sets up logging, and starts the bot.
    """
    # Set up logging
    log_dir = os.getenv("LOG_DIR")
    setup_logging(log_dir)

    logger = logging.getLogger(__name__)
    logger.info("Starting Discord announcement bot")

    # Get Discord token
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        return

    # Load settings
    config_path = os.getenv("CONFIG_PATH", "config.toml")
    settings_manager = SettingsManager(config_path)

    # Create and start bot
    bot = AnnouncementBot(settings_manager)

    try:
        logger.info("Connecting to Discord")
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    dotenv.load_dotenv()
    # Set up asyncio event loop
    asyncio.run(main())
