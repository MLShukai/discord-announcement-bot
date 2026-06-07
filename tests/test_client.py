# tests/test_client.py
"""Tests for the bot client's reaction handling and helpers."""

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from bot.client import AnnounceBotClient
from bot.constants import AnnouncementType, EnvKeys, ReactionEmoji
from tests.conftest import make_member


@pytest.fixture
def client(tmp_path, monkeypatch) -> AnnounceBotClient:
    """Construct a client with state/overrides redirected to tmp_path."""
    monkeypatch.setenv(EnvKeys.STATE_PATH, str(tmp_path / "state.json"))
    monkeypatch.setenv(EnvKeys.CONFIG_OVERRIDES_PATH, str(tmp_path / "overrides.toml"))
    return AnnounceBotClient()


def _payload(message_id: int, emoji: str, member) -> MagicMock:
    """Build a RawReactionActionEvent-like mock."""
    payload = MagicMock(spec=discord.RawReactionActionEvent)
    payload.message_id = message_id
    payload.user_id = 555
    payload.channel_id = 777
    payload.emoji = emoji
    payload.member = member
    return payload


def test_has_moderator_role(client):
    """Moderator/admin roles pass the guard; others do not."""
    assert client._has_moderator_role(make_member("Moderator")) is True
    assert client._has_moderator_role(make_member("告知管理者")) is True
    assert client._has_moderator_role(make_member("Member")) is False


@pytest.mark.asyncio
async def test_reaction_updates_type_when_authorized(client):
    """A moderator reaction on the confirm message updates the weekly type."""
    client.state.state.confirm_message_id = 12345
    client.state.state.session_type = AnnouncementType.WORKSPACE
    client.reannounce = AsyncMock()

    payload = _payload(12345, ReactionEmoji.REGULAR, make_member("Moderator"))
    await client.on_raw_reaction_add(payload)

    assert client.state.state.session_type == AnnouncementType.REGULAR


@pytest.mark.asyncio
async def test_reaction_triggers_reannounce(client):
    """An authorized type change re-announces the public message."""
    client.state.state.confirm_message_id = 12345
    client.state.state.session_type = AnnouncementType.REGULAR
    client.reannounce = AsyncMock()

    payload = _payload(12345, ReactionEmoji.WORKSPACE, make_member("Moderator"))
    await client.on_raw_reaction_add(payload)

    assert client.state.state.session_type == AnnouncementType.WORKSPACE
    client.reannounce.assert_awaited_once()


@pytest.mark.asyncio
async def test_reaction_ignored_for_other_message(client):
    """Reactions on a message other than the confirm report are ignored."""
    client.state.state.confirm_message_id = 12345
    client.state.state.session_type = AnnouncementType.REGULAR
    client.reannounce = AsyncMock()

    # 公開告知メッセージへのリアクションでは反応しない
    client.state.state.announce_message_id = 999
    payload = _payload(999, ReactionEmoji.REST, make_member("Moderator"))
    await client.on_raw_reaction_add(payload)

    assert client.state.state.session_type == AnnouncementType.REGULAR
    client.reannounce.assert_not_awaited()


@pytest.mark.asyncio
async def test_reaction_ignored_without_permission(client):
    """Reactions from members without a role are ignored."""
    client.state.state.confirm_message_id = 12345
    client.state.state.session_type = AnnouncementType.REGULAR
    client.reannounce = AsyncMock()

    payload = _payload(12345, ReactionEmoji.REST, make_member("Member"))
    await client.on_raw_reaction_add(payload)

    assert client.state.state.session_type == AnnouncementType.REGULAR
    client.reannounce.assert_not_awaited()


def test_action_role_mention_resolves_configured_role(client):
    """The configured action role is resolved to its mention string."""
    role = MagicMock(spec=discord.Role)
    role.name = "告知管理者"
    role.mention = "<@&42>"
    other = MagicMock(spec=discord.Role)
    other.name = "Member"
    guild = MagicMock(spec=discord.Guild)
    guild.roles = [other, role]

    assert client._action_role_mention(guild) == "<@&42>"


def test_action_role_mention_empty_when_role_absent(client):
    """An unresolved role yields an empty mention (no crash)."""
    guild = MagicMock(spec=discord.Guild)
    guild.roles = []
    assert client._action_role_mention(guild) == ""
    assert client._action_role_mention(None) == ""
