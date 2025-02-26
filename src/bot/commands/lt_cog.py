# src/bot/commands/lt_cog.py
"""LT情報管理のためのコマンドモジュール。"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ..client import AnnounceBotClient
from ..constants import ConfigKeys


class LtCog(commands.Cog):
    """LT情報を管理するためのコマンドコグ。

    発表者、タイトル、URLの設定・取得・クリア機能を提供する。
    """

    def __init__(self, bot: AnnounceBotClient):
        """LTコマンドコグを初期化する。

        Args:
            bot: Botクライアントインスタンス
        """
        self.bot = bot
        self.logger = logging.getLogger("announce-bot.commands.lt")

    def _check_lt_admin_permissions(self, interaction: discord.Interaction) -> bool:
        """ユーザーがLT情報を管理する権限を持っているか確認する。

        Args:
            interaction: 確認対象のインタラクション

        Returns:
            権限がある場合はTrue、ない場合はFalse
        """
        if not isinstance(interaction.user, discord.Member):
            return False

        # 設定から許可ロール名を取得
        admin_roles = self.bot.config.get(
            ConfigKeys.SECTION_PERMISSIONS,
            ConfigKeys.KEY_ADMIN_ROLES,
            ["Administrator"],
        )
        moderator_roles = self.bot.config.get(
            ConfigKeys.SECTION_PERMISSIONS,
            ConfigKeys.KEY_MODERATOR_ROLES,
            ["Moderator"],
        )
        lt_admin_roles = self.bot.config.get(
            ConfigKeys.SECTION_PERMISSIONS, ConfigKeys.KEY_LT_ADMIN_ROLES, ["LT管理者"]
        )

        allowed_roles = admin_roles + moderator_roles + lt_admin_roles

        # ユーザーが許可ロールを持っているか確認
        return any(role.name in allowed_roles for role in interaction.user.roles)

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
        # 現在の値を取得する場合
        if name is None:
            speaker = self.bot.announcement_service.lt_speaker
            await interaction.response.send_message(
                f"現在の発表者: {speaker or '未設定'}", ephemeral=True
            )
            return

        # 設定時は権限チェック
        if not self._check_lt_admin_permissions(interaction):
            await interaction.response.send_message(
                "LT情報を設定する権限がありません。", ephemeral=True
            )
            return

        # 新しい値を設定
        self.bot.announcement_service.lt_speaker = name
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
        # 現在の値を取得する場合
        if title is None:
            current_title = self.bot.announcement_service.lt_title
            await interaction.response.send_message(
                f"現在のタイトル: {current_title or '未設定'}", ephemeral=True
            )
            return

        # 設定時は権限チェック
        if not self._check_lt_admin_permissions(interaction):
            await interaction.response.send_message(
                "LT情報を設定する権限がありません。", ephemeral=True
            )
            return

        # 新しい値を設定
        self.bot.announcement_service.lt_title = title
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
        # 現在の値を取得する場合
        if url is None:
            current_url = self.bot.announcement_service.lt_url
            await interaction.response.send_message(
                f"現在のURL: {current_url or '未設定'}", ephemeral=True
            )
            return

        # 設定時は権限チェック
        if not self._check_lt_admin_permissions(interaction):
            await interaction.response.send_message(
                "LT情報を設定する権限がありません。", ephemeral=True
            )
            return

        # 新しい値を設定
        self.bot.announcement_service.lt_url = url
        await interaction.response.send_message(
            f"URLを '{url}' に設定しました。", ephemeral=True
        )

    @lt_group.command(name="info")
    async def lt_info(self, interaction: discord.Interaction):
        """現在のLT情報をすべて表示する。

        Args:
            interaction: コマンドインタラクション
        """
        lt_info = self.bot.announcement_service.lt_info

        if not any([lt_info.speaker_name, lt_info.title, lt_info.url]):
            await interaction.response.send_message(
                "LT情報は設定されていません。", ephemeral=True
            )
            return

        # 情報メッセージを構築
        info_parts: list[str] = []
        if lt_info.speaker_name is not None:
            info_parts.append(f"発表者: {lt_info.speaker_name}")
        if lt_info.title is not None:
            info_parts.append(f"タイトル: {lt_info.title}")
        if lt_info.url is not None:
            info_parts.append(f"URL: {lt_info.url}")

        # 完全性ステータスを追加
        is_complete = lt_info.is_complete
        status = "✅ 完全" if is_complete else "⚠️ 不完全"
        info_parts.append(f"ステータス: {status}")

        await interaction.response.send_message(
            "**現在のLT情報:**\n" + "\n".join(info_parts), ephemeral=True
        )

    @lt_group.command(name="clear")
    async def lt_clear(self, interaction: discord.Interaction):
        """すべてのLT情報をクリアする。

        Args:
            interaction: コマンドインタラクション
        """
        # 権限チェック
        if not self._check_lt_admin_permissions(interaction):
            await interaction.response.send_message(
                "LT情報をクリアする権限がありません。", ephemeral=True
            )
            return

        # LT情報をクリア
        self.bot.announcement_service.lt_info.clear()

        await interaction.response.send_message(
            "LT情報をクリアしました。", ephemeral=True
        )
        self.logger.info(f"LT情報が {interaction.user} によってクリアされました")

    @lt_speaker.error
    @lt_title.error
    @lt_url.error
    @lt_info.error
    @lt_clear.error
    async def lt_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """LTコマンドのエラーハンドラ。

        Args:
            interaction: コマンドインタラクション
            error: 発生したエラー
        """
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
        else:
            self.logger.error(f"LTコマンドでエラーが発生しました: {error}")
            await interaction.response.send_message(
                f"エラーが発生しました: {error}", ephemeral=True
            )
