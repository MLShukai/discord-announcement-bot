# src/bot/commands/utility_cog.py
"""Botの状態表示・ヘルプ・プレビュー機能を提供するコマンドモジュール。"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ..client import AnnounceBotClient
from ..constants import TYPE_BY_SLUG, AnnouncementType, ConfigKeys, Weekday
from ..scheduler import compute_next_run
from .permissions import is_admin

_TYPE_CHOICES = list(TYPE_BY_SLUG.keys())

HELP_TEXT = """**Discord告知Bot - コマンドヘルプ**

**運用の流れ:**
日曜に告知チャンネルへ「初回告知」を自動投稿 → 確認チャンネルへ報告 → 確認チャンネルのリアクション/`/plan set` で種別を変更すると公開告知を再投稿 → 開催時に `/open`

**今週の予定:**
`/plan show` - 今週の種別とLT情報を表示
`/plan set <type>` - 種別を変更 (regular/lt/workspace/rest)
`/open` - 開催告知を送信 (おやすみの週は送信しない)

**LT情報:**
`/lt set <title> <speaker> [url]` - LT情報を一括設定
`/lt speaker|title|url [値]` - 個別に設定/表示
`/lt info` / `/lt clear` - 表示 / クリア

**設定:**
`/config announce <day> <time>` - 初回告知の曜日・時刻
`/config event <day> <time>` - 開催の曜日・時刻
`/config role [role]` - アクションロール
`/config channel announce [channel]` - 公開告知チャンネル
`/config channel confirm [channel]` - 確認チャンネル (運営用)
`/config show` / `/config reset` - 表示 / リセット

**その他:**
`/status` - 次回予定と今週の種別を表示
`/manual announce` - 初回告知を手動送信
`/test announce|open [type]` - メッセージのプレビュー
`/help` - このヘルプ"""


class UtilityCog(commands.Cog):
    """ユーティリティコマンドを提供するコグ。

    状態表示・ヘルプ・プレビューコマンドを提供する。
    """

    def __init__(self, bot: AnnounceBotClient):
        """ユーティリティコマンドコグを初期化する。

        Args:
            bot: Botクライアントインスタンス
        """
        self.bot = bot
        self.logger = logging.getLogger("announce-bot.commands.utility")

    @app_commands.command(name="status")
    async def status(self, interaction: discord.Interaction):
        """次回の告知予定と今週の種別を表示する。

        Args:
            interaction: コマンドインタラクション
        """
        config = self.bot.config
        announce_weekday = config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, "Sun"
        )
        announce_time = config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME, "12:00"
        )
        hour, minute = map(int, announce_time.split(":"))
        next_announce = compute_next_run(
            self.bot.clock.now(), Weekday.to_int(announce_weekday), hour, minute
        )
        event_date = self.bot.announcement_service.next_event_date()
        state = self.bot.state.state

        status_parts = [
            "**ボットステータス:**",
            f"次回初回告知: {next_announce.month}/{next_announce.day} "
            f"({Weekday.to_jp(next_announce.weekday())}) {announce_time}",
            f"次回開催日: {event_date.month}/{event_date.day} "
            f"({Weekday.to_jp(event_date.weekday())})",
            f"今週の種別: {state.session_type}",
        ]
        if state.session_type == AnnouncementType.LIGHTNING_TALK:
            status = "✅ 完全" if state.lt.is_complete else "⚠️ 不完全"
            status_parts.append(f"\n**LT情報** ({status}):\n{state.lt}")

        await interaction.response.send_message("\n".join(status_parts), ephemeral=True)

    @app_commands.command(name="help")
    async def help_command(self, interaction: discord.Interaction):
        """Botコマンドのヘルプを表示する。

        Args:
            interaction: コマンドインタラクション
        """
        await interaction.response.send_message(HELP_TEXT, ephemeral=True)

    test_group = app_commands.Group(name="test", description="メッセージのプレビュー")

    @test_group.command(name="announce")
    @app_commands.describe(type="プレビューする種別 (省略時は今週の種別)")
    async def test_announce(
        self, interaction: discord.Interaction, type: str | None = None
    ):
        """初回告知メッセージをプレビューする（送信しない）。

        Args:
            interaction: コマンドインタラクション
            type: プレビューする種別スラッグ、または None で今週の種別
        """
        if not is_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
            return

        announcement_type = self._resolve_type(type)
        content = self.bot.announcement_service.build_announce(announcement_type)
        await interaction.response.send_message(
            f"**初回告知プレビュー ({announcement_type}):**\n\n{content}",
            ephemeral=True,
        )

    @test_group.command(name="open")
    @app_commands.describe(type="プレビューする種別 (省略時は今週の種別)")
    async def test_open(
        self, interaction: discord.Interaction, type: str | None = None
    ):
        """開催告知メッセージをプレビューする（送信しない）。

        Args:
            interaction: コマンドインタラクション
            type: プレビューする種別スラッグ、または None で今週の種別
        """
        if not is_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
            return

        announcement_type = self._resolve_type(type)
        content = self.bot.announcement_service.build_open(announcement_type)
        if content is None:
            await interaction.response.send_message(
                f"「{announcement_type}」には開催告知がありません。", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"**開催告知プレビュー ({announcement_type}):**\n\n{content}",
            ephemeral=True,
        )

    def _resolve_type(self, slug: str | None) -> AnnouncementType:
        """種別スラッグを開催種別に解決する（None なら今週の種別）。

        Args:
            slug: 種別スラッグ、または None

        Returns:
            解決された開催種別
        """
        if slug is None:
            return self.bot.state.state.session_type
        return TYPE_BY_SLUG.get(slug.lower(), self.bot.state.state.session_type)

    @test_announce.autocomplete("type")
    @test_open.autocomplete("type")
    async def type_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """種別スラッグのオートコンプリートを提供する。

        Args:
            interaction: インタラクション
            current: 現在の入力値

        Returns:
            一致する種別の選択肢リスト
        """
        return [
            app_commands.Choice(name=slug, value=slug)
            for slug in _TYPE_CHOICES
            if current.lower() in slug.lower()
        ]

    @status.error
    @help_command.error
    @test_announce.error
    @test_open.error
    async def utility_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """ユーティリティコマンドのエラーハンドラ。

        Args:
            interaction: コマンドインタラクション
            error: 発生したエラー
        """
        self.logger.error(f"ユーティリティコマンドでエラーが発生しました: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"エラーが発生しました: {error}", ephemeral=True
            )
