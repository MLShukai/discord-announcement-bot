# tests/config/test_config_manager.py
"""Tests for the configuration manager module."""

from unittest.mock import mock_open, patch

import pytest

from bot.config.config_manager import ConfigManager

# Sample configuration data for testing
SAMPLE_CONFIG = {
    "settings": {
        "confirm_time": "21:30",
        "announce_time": "21:30",
        "action_role": "@everyone",
        "confirm_weekday": "Thu",
        "announce_weekday": "Sun",
    },
    "channels": {
        "action_channel_id": "",
        "announce_channel_id": "",
    },
}

SAMPLE_OVERRIDES = {
    "settings": {
        "confirm_time": "20:00",
    },
    "channels": {
        "action_channel_id": "123456789",
    },
}


@pytest.fixture
def mock_config_files():
    """Create mocks for file operations used by ConfigManager."""
    with (
        patch("builtins.open", mock_open()),
        patch("os.path.exists", return_value=True),
        patch("tomllib.load", side_effect=[SAMPLE_CONFIG, SAMPLE_OVERRIDES]),
        patch("tomli_w.dump") as dump_mock,
        patch("os.makedirs"),
    ):
        yield dump_mock


@pytest.fixture
def config_manager(mock_config_files):
    """Create a ConfigManager with mocked file operations."""
    return ConfigManager("config.toml", "overrides.toml")


def test_config_manager_init():
    """Test ConfigManager initialization with various paths."""
    # Test with explicit paths
    with (
        patch("builtins.open", mock_open()),
        patch("os.path.exists", return_value=True),
        patch("tomllib.load", return_value={}),
    ):
        manager = ConfigManager("custom.toml", "custom-overrides.toml")
        assert manager.config_path == "custom.toml"
        assert manager.overrides_path == "custom-overrides.toml"

    # Test with default paths from environment variables
    with (
        patch("builtins.open", mock_open()),
        patch("os.path.exists", return_value=True),
        patch("tomllib.load", return_value={}),
        patch("os.getenv", side_effect=["env_config.toml", "env_overrides.toml"]),
    ):
        manager = ConfigManager()
        assert manager.config_path == "env_config.toml"
        assert manager.overrides_path == "env_overrides.toml"


def test_get_configuration_values(config_manager):
    """Test retrieving configuration values with different priorities."""
    # Get value from overrides (higher priority)
    assert config_manager.get("settings", "confirm_time", "default") == "20:00"

    # Get value from config (not in overrides)
    assert config_manager.get("settings", "announce_time", "default") == "21:30"

    # Get value from default (not in config or overrides)
    assert config_manager.get("non_existent", "key", "default_value") == "default_value"


def test_set_configuration_values(config_manager, mock_config_files):
    """Test setting configuration values."""
    # Set a new value
    config_manager.set("settings", "new_setting", "new_value")
    assert config_manager.overrides["settings"]["new_setting"] == "new_value"
    assert mock_config_files.called

    # Update an existing value
    mock_config_files.reset_mock()
    config_manager.set("settings", "confirm_time", "22:00")
    assert config_manager.overrides["settings"]["confirm_time"] == "22:00"
    assert mock_config_files.called


def test_set_to_default_value(config_manager, mock_config_files):
    """Test setting a value to its default removes it from overrides."""
    # Set a value to its default in config
    config_manager.set("settings", "confirm_time", "21:30")
    assert "confirm_time" not in config_manager.overrides["settings"]
    assert mock_config_files.called


def test_reset_all_settings(config_manager):
    """Test resetting all configuration settings."""
    with (
        patch("os.path.exists", return_value=True),
        patch("os.remove") as remove_mock,
        patch("tomli_w.dump"),
    ):
        config_manager.reset()
        assert config_manager.overrides == {}
        assert remove_mock.called
