"""Tests for the settings module."""

import tempfile
import tomllib
from datetime import time
from pathlib import Path

from bot.config.settings import (
    BotSettings,
    EventType,
    LightningTalkInfo,
    SettingsManager,
)


class TestLightningTalkInfo:
    """Tests for the LightningTalkInfo class."""

    def test_init_default(self):
        """Test default initialization."""
        lt_info = LightningTalkInfo()
        assert lt_info.speaker == ""
        assert lt_info.title == ""
        assert lt_info.url == ""

    def test_init_with_values(self):
        """Test initialization with values."""
        lt_info = LightningTalkInfo(
            speaker="Test Speaker", title="Test Title", url="https://example.com"
        )
        assert lt_info.speaker == "Test Speaker"
        assert lt_info.title == "Test Title"
        assert lt_info.url == "https://example.com"

    def test_clear(self):
        """Test clearing information."""
        lt_info = LightningTalkInfo(
            speaker="Test Speaker", title="Test Title", url="https://example.com"
        )
        lt_info.clear()
        assert lt_info.speaker == ""
        assert lt_info.title == ""
        assert lt_info.url == ""

    def test_is_complete(self):
        """Test checking if information is complete."""
        # Empty
        lt_info = LightningTalkInfo()
        assert not lt_info.is_complete()

        # Partial
        lt_info.speaker = "Test Speaker"
        assert not lt_info.is_complete()

        lt_info.title = "Test Title"
        assert not lt_info.is_complete()

        # Complete
        lt_info.url = "https://example.com"
        assert lt_info.is_complete()


class TestBotSettings:
    """Tests for the BotSettings class."""

    def test_init_default(self):
        """Test default initialization."""
        settings = BotSettings()
        assert settings.announce_time == time(21, 30)
        assert settings.confirm_time == time(21, 30)
        assert settings.action_role == "@GesonAnko"
        assert settings.confirm_weekday == "Thu"
        assert settings.announce_weekday == "Sun"
        assert (
            settings.default_url
            == "https://x.com/VRC_ML_hangout/status/1779863235988242925"
        )
        assert settings.action_channel_id == 0
        assert settings.announce_channel_id == 0
        assert settings.command_channel_id == 0
        assert settings.lt_info.speaker == ""
        assert settings.lt_info.title == ""
        assert settings.lt_info.url == ""
        assert settings.next_event_type == EventType.REGULAR


class TestSettingsManager:
    """Tests for the SettingsManager class."""

    def test_init(self):
        """Test initialization."""
        manager = SettingsManager("test_config.toml")
        assert manager.config_path == Path("test_config.toml")
        assert isinstance(manager.settings, BotSettings)

    def test_load_nonexistent_file(self):
        """Test loading from a nonexistent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.toml"
            manager = SettingsManager(str(config_path))
            settings = manager.load()

            # Should return default settings
            assert settings.announce_time == time(21, 30)
            assert settings.confirm_time == time(21, 30)

    def test_load_existing_file(self, tmpdir):
        """Test loading from an existing file."""
        # Create a test config file
        config_path = Path(tmpdir) / "test_config.toml"
        config_content = """
        announce_time = "20:00"
        confirm_time = "18:30"
        action_role = "@TestRole"
        confirm_weekday = "Mon"
        announce_weekday = "Wed"
        default_url = "https://example.com"
        action_channel_id = 123456789
        announce_channel_id = 987654321
        command_channel_id = 123123123
        """

        with open(config_path, "w") as f:
            f.write(config_content)

        # Load settings
        manager = SettingsManager(str(config_path))
        settings = manager.load()

        # Check values
        assert settings.announce_time == time(20, 0)
        assert settings.confirm_time == time(18, 30)
        assert settings.action_role == "@TestRole"
        assert settings.confirm_weekday == "Mon"
        assert settings.announce_weekday == "Wed"
        assert settings.default_url == "https://example.com"
        assert settings.action_channel_id == 123456789
        assert settings.announce_channel_id == 987654321
        assert settings.command_channel_id == 123123123

    def test_save(self, tmpdir):
        """Test saving settings to a file."""
        config_path = Path(tmpdir) / "test_config.toml"
        manager = SettingsManager(str(config_path))

        # Modify settings
        manager.settings.announce_time = time(19, 45)
        manager.settings.confirm_time = time(17, 15)
        manager.settings.action_role = "@ModifiedRole"
        manager.settings.action_channel_id = 555555555

        # Save settings
        result = manager.save()
        assert result is True

        # Check file exists
        assert config_path.exists()

        # Load and verify content
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        assert data["announce_time"] == "19:45"
        assert data["confirm_time"] == "17:15"
        assert data["action_role"] == "@ModifiedRole"
        assert data["action_channel_id"] == 555555555

        # Runtime data should not be saved
        assert "lt_info" not in data
        assert "next_event_type" not in data
