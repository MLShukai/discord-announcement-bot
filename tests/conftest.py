"""Test fixtures for the Discord announcement bot."""

import asyncio
from datetime import time
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from discord import Client, Guild, Message, Reaction, TextChannel, User

from bot.config.settings import (
    BotSettings,
    EventType,
    LightningTalkInfo,
    SettingsManager,
)


@pytest.fixture
def settings():
    """Create test settings."""
    settings = BotSettings()
    settings.action_channel_id = 12345
    settings.announce_channel_id = 67890
    settings.command_channel_id = 54321
    return settings


@pytest.fixture
def settings_manager(settings, tmp_path):
    """Create test settings manager."""
    config_path = tmp_path / "test_config.toml"
    manager = SettingsManager(str(config_path))
    manager.settings = settings
    return manager


class MockChannel(MagicMock):
    """Mock Discord channel."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = kwargs.get("id", 12345)
        self.name = kwargs.get("name", "test-channel")
        self.send = AsyncMock(return_value=MockMessage())
        self.mention = f"<#{self.id}>"


class MockUser(MagicMock):
    """Mock Discord user."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = kwargs.get("id", 98765)
        self.name = kwargs.get("name", "test-user")
        self.bot = kwargs.get("bot", False)
        self.mention = f"<@{self.id}>"


class MockMessage(MagicMock):
    """Mock Discord message."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = kwargs.get("id", 111222)
        self.content = kwargs.get("content", "")
        self.author = kwargs.get("author", MockUser())
        self.channel = kwargs.get("channel", MockChannel())
        self.guild = kwargs.get("guild", MockGuild())
        self.add_reaction = AsyncMock()


class MockReaction(MagicMock):
    """Mock Discord reaction."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.emoji = kwargs.get("emoji", "👍")
        self.message = kwargs.get("message", MockMessage())
        self.count = kwargs.get("count", 1)


class MockGuild(MagicMock):
    """Mock Discord guild."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = kwargs.get("id", 333444)
        self.name = kwargs.get("name", "test-guild")
        self.channels = {}

    def get_channel(self, channel_id):
        """Get a channel by ID."""
        return self.channels.get(channel_id)


class MockClient(MagicMock):
    """Mock Discord client."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = MockUser(name="bot", bot=True)
        self.guilds = [MockGuild()]
        self.channels = {}

    def get_channel(self, channel_id):
        """Get a channel by ID."""
        return self.channels.get(channel_id)


@pytest.fixture
def mock_client():
    """Create a mock Discord client."""
    client = MockClient()

    # Add channels
    action_channel = MockChannel(id=12345, name="action-channel")
    announce_channel = MockChannel(id=67890, name="announce-channel")
    command_channel = MockChannel(id=54321, name="command-channel")

    client.channels = {
        12345: action_channel,
        67890: announce_channel,
        54321: command_channel,
    }

    client.guilds[0].channels = client.channels

    return client


@pytest.fixture
def mock_message():
    """Create a mock Discord message."""
    return MockMessage()


@pytest.fixture
def mock_reaction():
    """Create a mock Discord reaction."""
    return MockReaction()


@pytest.fixture
def event_loop():
    """Create an asyncio event loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
