# src/bot/commands/manual_cog.py
"""手動実行コマンドを提供するモジュール。"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ..client import AnnounceBotClient
from ..constants import AnnouncementType, ConfigKeys


class ManualCog(commands.Cog):
    """手動実行コマンドを提供するコグ。

    確認メッセージと告知メッセージを手動で送信するコマンドを提供する。
    """

    def __init__(self, bot: AnnounceBotClient):
        """手動実行コマンドコグを初期化する。

        Args:
            bot: Botクライアントインスタンス
        """
        self.bot = bot
        self.logger = logging.getLogger("announce-bot.commands.manual")

    def _check_admin_permissions(self, interaction: discord.Interaction) -> bool:
        """ユーザーが手動実行コマンドを実行する権限を持っているか確認する。

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

        allowed_roles = admin_roles + moderator_roles

        # ユーザーが許可ロールを持っているか確認
        return any(role.name in allowed_roles for role in interaction.user.roles)

    manual_group = app_commands.Group(name="manual", description="手動実行コマンド")

    @manual_group.command(name="confirm")
    async def manual_confirm(self, interaction: discord.Interaction) -> None:
        """確認メッセージを手動で送信する。

        Args:
            interaction: コマンドインタラクション
        """
        # 権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
            return

        # アクションチャンネルを取得
        action_channel_id = self.bot.config.get(
            ConfigKeys.SECTION_CHANNELS, ConfigKeys.KEY_ACTION_CHANNEL_ID, ""
        )
        if not action_channel_id:
            await interaction.response.send_message(
                "アクションチャンネルが設定されていません。`/config channel action` で設定してください。",
                ephemeral=True,
            )
            return

        action_channel = self.bot.get_channel(int(action_channel_id))
        if not action_channel:
            await interaction.response.send_message(
                f"アクションチャンネル (ID: {action_channel_id}) が見つかりません。",
                ephemeral=True,
            )
            return
        if not isinstance(action_channel, discord.TextChannel):
            return

        # アクションロールを取得
        action_role_name = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ACTION_ROLE, ""
        )
        action_role = None

        if action_role_name:
            # @が含まれている場合は削除
            clean_role_name = action_role_name.lstrip("@")

            guild = action_channel.guild
            action_role = discord.utils.get(guild.roles, name=clean_role_name)

            if not action_role:
                self.logger.warning(
                    f"ロール {clean_role_name} がギルドに見つかりません"
                )

        # レスポンスを遅延
        await interaction.response.defer(ephemeral=True)

        # 確認メッセージを送信
        message = await self.bot.announcement_service.send_confirmation(
            action_channel, action_role
        )

        if message:
            await interaction.followup.send(
                f"確認メッセージを {action_channel.mention} に送信しました。",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "確認メッセージの送信に失敗しました。", ephemeral=True
            )

    @manual_group.command(name="announce")
    @app_commands.describe(type="アナウンスの種類")
    async def manual_announce(
        self, interaction: discord.Interaction, type: str = "regular"
    ):
        """告知メッセージを手動で送信する。

        Args:
            interaction: コマンドインタラクション
            type: 送信する告知の種類（regular, lt, rest）
        """
        # 権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
            return

        # 告知チャンネルを取得
        announce_channel_id = self.bot.config.get(
            ConfigKeys.SECTION_CHANNELS, ConfigKeys.KEY_ANNOUNCE_CHANNEL_ID, ""
        )
        if not announce_channel_id:
            await interaction.response.send_message(
                "告知チャンネルが設定されていません。`/config channel announce` で設定してください。",
                ephemeral=True,
            )
            return

        announce_channel = self.bot.get_channel(int(announce_channel_id))
        if not announce_channel:
            await interaction.response.send_message(
                f"告知チャンネル (ID: {announce_channel_id}) が見つかりません。",
                ephemeral=True,
            )
            return
        if not isinstance(announce_channel, discord.TextChannel):
            return

        # タイプを列挙型にマッピング
        type_map = {
            "regular": AnnouncementType.REGULAR,
            "lt": AnnouncementType.LIGHTNING_TALK,
            "rest": AnnouncementType.REST,
        }

        announcement_type = type_map.get(type.lower(), AnnouncementType.REGULAR)

        # LT告知の場合はLT情報が完全かチェック
        if (
            announcement_type == AnnouncementType.LIGHTNING_TALK
            and not self.bot.announcement_service.lt_info.is_complete
        ):
            await interaction.response.send_message(
                "LT情報が不完全です。`/lt info` で確認し、`/lt speaker`、`/lt title`、`/lt url` で設定してください。",
                ephemeral=True,
            )
            return

        # レスポンスを遅延
        await interaction.response.defer(ephemeral=True)

        # 告知メッセージを送信
        message = await self.bot.announcement_service.send_announcement(
            announce_channel, announcement_type
        )

        if message:
            await interaction.followup.send(
                f"{type} 告知メッセージを {announce_channel.mention} に送信しました。",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "告知メッセージの送信に失敗しました。", ephemeral=True
            )

    @manual_announce.autocomplete("type")
    async def manual_announce_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """告知タイプのオートコンプリートを提供する。

        Args:
            interaction: インタラクション
            current: 現在の入力値

        Returns:
            一致するタイプの選択肢リスト
        """
        types = ["regular", "lt", "rest"]
        return [
            app_commands.Choice(name=t, value=t)
            for t in types
            if current.lower() in t.lower()
        ]

    @manual_confirm.error
    @manual_announce.error
    async def manual_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """手動実行コマンドのエラーハンドラ。

        Args:
            interaction: コマンドインタラクション
            error: 発生したエラー
        """
        self.logger.error(f"手動実行コマンドでエラーが発生しました: {error}")
        await interaction.response.send_message(
            f"エラーが発生しました: {error}", ephemeral=True
        )
