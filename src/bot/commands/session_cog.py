# src/bot/commands/session_cog.py
"""今週の開催種別の管理と、開催告知 (/open) を提供するコマンドモジュール。"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ..client import AnnounceBotClient
from ..constants import TYPE_BY_SLUG, AnnouncementType
from .permissions import is_admin

# 種別スラッグのオートコンプリート候補
_TYPE_CHOICES = list(TYPE_BY_SLUG.keys())


class SessionCog(commands.Cog):
    """今週の予定 (`/plan`)・開催告知 (`/open`)・手動初回告知を提供するコグ。"""

    def __init__(self, bot: AnnounceBotClient):
        """セッションコマンドコグを初期化する。

        Args:
            bot: Botクライアントインスタンス
        """
        self.bot = bot
        self.logger = logging.getLogger("announce-bot.commands.session")

    plan_group = app_commands.Group(name="plan", description="今週の予定の管理")

    @plan_group.command(name="show")
    async def plan_show(self, interaction: discord.Interaction) -> None:
        """今週の予定 (開催種別とLT情報) を表示する。

        Args:
            interaction: コマンドインタラクション
        """
        state = self.bot.state.state
        parts = [f"**今週の予定:** {state.session_type}"]
        if state.session_type == AnnouncementType.LIGHTNING_TALK:
            status = "✅ 完全" if state.lt.is_complete else "⚠️ 不完全"
            parts.append(f"\n**LT情報** ({status}):\n{state.lt}")
        await interaction.response.send_message("\n".join(parts), ephemeral=True)

    @plan_group.command(name="set")
    @app_commands.describe(type="開催種別 (regular / lt / workspace / rest)")
    async def plan_set(self, interaction: discord.Interaction, type: str) -> None:
        """今週の開催種別を設定する。

        Args:
            interaction: コマンドインタラクション
            type: 設定する種別スラッグ
        """
        if not is_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "予定を変更する権限がありません。", ephemeral=True
            )
            return

        announcement_type = TYPE_BY_SLUG.get(type.lower())
        if announcement_type is None:
            await interaction.response.send_message(
                f"無効な種別です。有効な値: {', '.join(_TYPE_CHOICES)}",
                ephemeral=True,
            )
            return

        self.bot.state.state.session_type = announcement_type
        self.bot.state.save()
        self.logger.info(
            f"{interaction.user} が種別を {announcement_type} に変更しました"
        )

        message = f"今週の予定を「{announcement_type}」に設定しました。"
        if (
            announcement_type == AnnouncementType.LIGHTNING_TALK
            and not self.bot.state.state.lt.is_complete
        ):
            message += "\n⚠️ LT情報が不完全です。`/lt set` で設定してください。"
        await interaction.response.send_message(message, ephemeral=True)

    @plan_set.autocomplete("type")
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

    @app_commands.command(name="open")
    async def open_command(self, interaction: discord.Interaction) -> None:
        """インスタンスを開けた際に開催告知を送信する。

        おやすみの週は警告のみで何も送信しない。

        Args:
            interaction: コマンドインタラクション
        """
        if not is_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
            return

        session_type = self.bot.state.state.session_type
        if session_type == AnnouncementType.REST:
            await interaction.response.send_message(
                "今週はおやすみのため、開催告知は送信しません。", ephemeral=True
            )
            return

        if (
            session_type == AnnouncementType.LIGHTNING_TALK
            and not self.bot.state.state.lt.is_complete
        ):
            await interaction.response.send_message(
                "LT情報が不完全です。`/lt set` で発表者・タイトル・URLを設定してください。",
                ephemeral=True,
            )
            return

        channel = self.bot.get_announce_channel()
        if channel is None:
            await interaction.response.send_message(
                "告知チャンネルが設定されていません。`/config channel announce` で設定してください。",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        message = await self.bot.announcement_service.send_open(channel)
        if message:
            await interaction.followup.send(
                f"開催告知を {channel.mention} に送信しました。", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "開催告知の送信に失敗しました。", ephemeral=True
            )

    manual_group = app_commands.Group(name="manual", description="手動実行コマンド")

    @manual_group.command(name="announce")
    async def manual_announce(self, interaction: discord.Interaction) -> None:
        """初回告知を手動で送信する（スケジュールと同じ処理）。

        Args:
            interaction: コマンドインタラクション
        """
        if not is_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
            return

        channel = self.bot.get_announce_channel()
        if channel is None:
            await interaction.response.send_message(
                "告知チャンネルが設定されていません。`/config channel announce` で設定してください。",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        await self.bot.run_weekly_announce()
        await interaction.followup.send(
            f"初回告知を {channel.mention} に送信しました。", ephemeral=True
        )

    @plan_show.error
    @plan_set.error
    @open_command.error
    @manual_announce.error
    async def session_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """セッションコマンドのエラーハンドラ。

        Args:
            interaction: コマンドインタラクション
            error: 発生したエラー
        """
        self.logger.error(f"セッションコマンドでエラーが発生しました: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"エラーが発生しました: {error}", ephemeral=True
            )
