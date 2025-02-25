"""Settings module for loading and saving bot configuration.

This module handles all configuration management for the Discord
announcement bot, including loading from and saving to TOML files, and
providing default values.
"""

import tomllib
from dataclasses import asdict, dataclass, field
from datetime import time
from enum import Enum, auto
from pathlib import Path

import tomli_w


class EventType(Enum):
    """Enum representing the types of events that can be announced."""

    REGULAR = auto()
    LIGHTNING_TALK = auto()
    REST = auto()


@dataclass
class LightningTalkInfo:
    """Container for Lightning Talk information.

    Stores the speaker name, talk title, and URL for a Lightning Talk
    event.
    """

    speaker: str = ""
    title: str = ""
    url: str = ""

    def clear(self) -> None:
        """Clear all Lightning Talk information."""
        self.speaker = ""
        self.title = ""
        self.url = ""

    def is_complete(self) -> bool:
        """Check if all required Lightning Talk information is set.

        Returns:
            True if speaker, title, and URL are all non-empty, False otherwise.
        """
        return bool(self.speaker and self.title and self.url)


@dataclass
class BotSettings:
    """Container for all bot settings.

    Stores and manages all configuration options for the Discord
    announcement bot.
    """

    # Default values
    announce_time: time = field(default_factory=lambda: time(21, 30))
    confirm_time: time = field(default_factory=lambda: time(21, 30))
    action_role: str = "@GesonAnko"
    confirm_weekday: str = "Thu"
    announce_weekday: str = "Sun"
    default_url: str = "https://x.com/VRC_ML_hangout/status/1779863235988242925"
    action_channel_id: int = 0
    announce_channel_id: int = 0
    command_channel_id: int = 0

    # Runtime data (not stored in config file)
    lt_info: LightningTalkInfo = field(default_factory=LightningTalkInfo)
    next_event_type: EventType = EventType.REGULAR


class SettingsManager:
    """Manager for loading and saving bot settings.

    Handles the persistence of bot settings to and from TOML files.
    """

    def __init__(self, config_path: str | None = None):
        """Initialize the settings manager.

        Args:
            config_path: Path to the configuration file. If None, uses the default path.
        """
        self.config_path = Path(config_path or "config.toml")
        self.settings = BotSettings()

    def load(self) -> BotSettings:
        """Load settings from the TOML file.

        Returns:
            The loaded settings, or default settings if the file doesn't exist.
        """
        if not self.config_path.exists():
            return self.settings

        try:
            with open(self.config_path, "rb") as f:
                config_data = tomllib.load(f)

            # Update settings with values from config file
            for key, value in config_data.items():
                if key in ["announce_time", "confirm_time"]:
                    hour, minute = map(int, value.split(":"))
                    setattr(self.settings, key, time(hour, minute))
                elif hasattr(self.settings, key):
                    setattr(self.settings, key, value)

            return self.settings
        except Exception as e:
            # Log the error and return default settings
            print(f"Error loading settings: {e}")
            return self.settings

    def save(self) -> bool:
        """Save settings to the TOML file.

        Returns:
            True if saving was successful, False otherwise.
        """
        try:
            # Convert settings to dict, excluding runtime data
            settings_dict = {
                k: v
                for k, v in asdict(self.settings).items()
                if k not in ["lt_info", "next_event_type"]
            }

            # Convert time objects to strings
            for k, v in settings_dict.items():
                if isinstance(v, time):
                    settings_dict[k] = f"{v.hour:02d}:{v.minute:02d}"

            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to TOML file
            with open(self.config_path, "wb") as f:
                tomli_w.dump(settings_dict, f)

            return True
        except Exception as e:
            # Log the error
            print(f"Error saving settings: {e}")
            return False
