# tests/conftest.py
"""テスト共通のフィクスチャ。

実 `ConfigManager` / `StateStore` を tmp_path 上で使い、Discord API のみモックする。
時刻は `FixedClock` で決定化する。
"""

import datetime
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from bot.announcement.service import AnnouncementService
from bot.config import ConfigManager
from bot.state import StateStore

# 2026-06-07 は日曜日。次の水曜開催日は 2026-06-10。
FIXED_NOW = datetime.datetime(2026, 6, 7, 12, 0)


class FixedClock:
    """固定時刻を返すテスト用 Clock。"""

    def __init__(self, now: datetime.datetime = FIXED_NOW):
        self._now = now

    def now(self) -> datetime.datetime:
        return self._now

    def today(self) -> datetime.date:
        return self._now.date()


@pytest.fixture
def clock() -> FixedClock:
    """固定時刻の Clock を返す。"""
    return FixedClock()


@pytest.fixture
def config(tmp_path) -> ConfigManager:
    """リポジトリの config.toml を読み、override は tmp_path に書く ConfigManager。"""
    overrides = tmp_path / "config-overrides.toml"
    return ConfigManager("config.toml", str(overrides))


@pytest.fixture
def state(tmp_path) -> StateStore:
    """tmp_path 上の状態ストア。"""
    return StateStore(str(tmp_path / "state.json"))


@pytest.fixture
def service(config, state, clock) -> AnnouncementService:
    """固定時刻・実 config・実 state を注入した告知サービス。"""
    return AnnouncementService(config, state, clock)


@pytest.fixture
def mock_bot(config, state, service, clock) -> MagicMock:
    """Cog テスト用の Bot スタブ（実 config / state / service を保持）。"""
    bot = MagicMock()
    bot.config = config
    bot.state = state
    bot.announcement_service = service
    bot.clock = clock
    bot.reannounce = AsyncMock()
    return bot


def make_member(*role_names: str) -> MagicMock:
    """指定ロール名を持つ `discord.Member` のモックを作る。

    Args:
        role_names: 付与するロール名

    Returns:
        roles を備えたメンバーのモック
    """
    member = MagicMock(spec=discord.Member)
    member.roles = [MagicMock(name=name) for name in role_names]
    # MagicMock(name=...) は表示名であって .name 属性ではないため明示的に設定する
    for role, name in zip(member.roles, role_names):
        role.name = name
    return member


def make_interaction(member: MagicMock | None = None) -> AsyncMock:
    """コマンドテスト用の `discord.Interaction` モックを作る。

    Args:
        member: コマンド実行者（省略時はロール無しメンバー）

    Returns:
        response をモックしたインタラクション
    """
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.followup = AsyncMock()
    interaction.user = member if member is not None else make_member()
    return interaction
