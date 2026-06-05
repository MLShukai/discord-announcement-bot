# src/bot/commands/lt_cog.py
"""LT情報管理のためのコマンドモジュール。"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ..client import AnnounceBotClient
from ..constants import ConfigKeys
from ..state import LTInfo
from .permissions import is_lt_admin


class LtCog(commands.Cog):
    """LT情報を管理するためのコマンドコグ。

    発表者・タイトル・URLの設定・取得・クリア機能を提供する。
    """

    def __init__(self, bot: AnnounceBotClient):
        """LTコマンドコグを初期化する。

        Args:
            bot: Botクライアントインスタンス
        """
        self.bot = bot
        self.logger = logging.getLogger("announce-bot.commands.lt")

    @property
    def _lt(self) -> LTInfo:
        """現在のLT情報を返す（状態ストア経由）。"""
        return self.bot.state.state.lt

    def _save(self) -> None:
        """状態を永続化する。"""
        self.bot.state.save()

    lt_group = app_commands.Group(name="lt", description="LT情報の管理")

    @lt_group.command(name="speaker")
    @app_commands.describe(name="発表者の名前")
    async def lt_speaker(
        self, interaction: discord.Interaction, name: str | None = None
    ):
        """LT発表者名を設定または取得する。

        Args:
            interaction: コマンドインタラクション
            name: 設定する発表者名、またはNoneで現在の値を取得
        """
        if name is None:
            await interaction.response.send_message(
                f"現在の発表者: {self._lt.speaker_name or '未設定'}", ephemeral=True
            )
            return

        if not is_lt_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "LT情報を設定する権限がありません。", ephemeral=True
            )
            return

        self._lt.speaker_name = name
        self._save()
        await interaction.response.send_message(
            f"発表者を '{name}' に設定しました。", ephemeral=True
        )

    @lt_group.command(name="title")
    @app_commands.describe(title="発表のタイトル")
    async def lt_title(
        self, interaction: discord.Interaction, title: str | None = None
    ):
        """LTタイトルを設定または取得する。

        Args:
            interaction: コマンドインタラクション
            title: 設定するタイトル、またはNoneで現在の値を取得
        """
        if title is None:
            await interaction.response.send_message(
                f"現在のタイトル: {self._lt.title or '未設定'}", ephemeral=True
            )
            return

        if not is_lt_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "LT情報を設定する権限がありません。", ephemeral=True
            )
            return

        self._lt.title = title
        self._save()
        await interaction.response.send_message(
            f"タイトルを '{title}' に設定しました。", ephemeral=True
        )

    @lt_group.command(name="url")
    @app_commands.describe(url="発表またはイベントのURL")
    async def lt_url(self, interaction: discord.Interaction, url: str | None = None):
        """LT URLを設定または取得する。

        Args:
            interaction: コマンドインタラクション
            url: 設定するURL、またはNoneで現在の値を取得
        """
        if url is None:
            await interaction.response.send_message(
                f"現在のURL: {self._lt.url or '未設定'}", ephemeral=True
            )
            return

        if not is_lt_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "LT情報を設定する権限がありません。", ephemeral=True
            )
            return

        self._lt.url = url
        self._save()
        await interaction.response.send_message(
            f"URLを '{url}' に設定しました。", ephemeral=True
        )

    @lt_group.command(name="set")
    @app_commands.describe(
        title="発表のタイトル",
        speaker="発表者の名前",
        url="発表またはイベントのURL（省略時はデフォルトURL）",
    )
    async def lt_set(
        self,
        interaction: discord.Interaction,
        title: str,
        speaker: str,
        url: str | None = None,
    ):
        """LT情報を一度に設定する。

        Args:
            interaction: コマンドインタラクション
            title: 設定するタイトル
            speaker: 設定する発表者名
            url: 設定するURL（省略時はデフォルトURL）
        """
        if not is_lt_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "LT情報を設定する権限がありません。", ephemeral=True
            )
            return

        self._lt.title = title
        self._lt.speaker_name = speaker

        response_parts = [
            "LT情報を設定しました。",
            f"タイトル: {title}",
            f"発表者: {speaker}",
        ]
        if url is not None:
            self._lt.url = url
            response_parts.append(f"URL: {url}")
        else:
            default_url = self.bot.config.get(
                ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_DEFAULT_URL, ""
            )
            self._lt.url = default_url
            response_parts.append(f"URL: {default_url} (デフォルト)")

        self._save()
        await interaction.response.send_message(
            "\n".join(response_parts), ephemeral=True
        )

    @lt_group.command(name="info")
    async def lt_info(self, interaction: discord.Interaction):
        """現在のLT情報をすべて表示する。

        Args:
            interaction: コマンドインタラクション
        """
        lt = self._lt
        if not any([lt.speaker_name, lt.title, lt.url]):
            await interaction.response.send_message(
                "LT情報は設定されていません。", ephemeral=True
            )
            return

        status = "✅ 完全" if lt.is_complete else "⚠️ 不完全"
        await interaction.response.send_message(
            f"**現在のLT情報:**\n{lt}\nステータス: {status}", ephemeral=True
        )

    @lt_group.command(name="clear")
    async def lt_clear(self, interaction: discord.Interaction):
        """すべてのLT情報をクリアする。

        Args:
            interaction: コマンドインタラクション
        """
        if not is_lt_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "LT情報をクリアする権限がありません。", ephemeral=True
            )
            return

        self._lt.clear()
        self._save()
        await interaction.response.send_message(
            "LT情報をクリアしました。", ephemeral=True
        )
        self.logger.info(f"LT情報が {interaction.user} によってクリアされました")

    @lt_speaker.error
    @lt_title.error
    @lt_url.error
    @lt_info.error
    @lt_clear.error
    @lt_set.error
    async def lt_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """LTコマンドのエラーハンドラ。

        Args:
            interaction: コマンドインタラクション
            error: 発生したエラー
        """
        self.logger.error(f"LTコマンドでエラーが発生しました: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"エラーが発生しました: {error}", ephemeral=True
            )
