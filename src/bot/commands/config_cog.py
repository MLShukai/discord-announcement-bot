# src/bot/commands/config_cog.py
"""Bot設定管理のためのコマンドモジュール。"""

import logging
import re

import discord
from discord import app_commands
from discord.ext import commands

from ..client import AnnounceBotClient
from ..constants import ConfigKeys, Weekday
from .permissions import is_admin

_TIME_PATTERN = re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$")


class ConfigCog(commands.Cog):
    """Bot設定を管理するためのコマンドコグ。

    告知日時・開催日時・チャンネル・ロールなどの設定管理機能を提供する。
    """

    def __init__(self, bot: AnnounceBotClient):
        """設定コマンドコグを初期化する。

        Args:
            bot: Botクライアントインスタンス
        """
        self.bot = bot
        self.logger = logging.getLogger("announce-bot.commands.config")

    def _validate_day_time(self, day: str, time: str) -> str | None:
        """曜日と時刻のバリデーションを行う。

        Args:
            day: 3文字の曜日略称
            time: HH:MM形式の時刻

        Returns:
            エラーメッセージ。問題なければ None
        """
        if day not in Weekday.ALL:
            return f"無効な曜日形式です。有効な値: {', '.join(Weekday.ALL)}"
        if not _TIME_PATTERN.match(time):
            return "無効な時間形式です。HH:MM形式で入力してください。"
        return None

    config_group = app_commands.Group(name="config", description="ボットの設定を管理")

    @config_group.command(name="announce")
    @app_commands.describe(
        day="初回告知の曜日 (Mon, Tue, ..., Sun)",
        time="初回告知の時刻 (HH:MM形式)",
    )
    async def config_announce(
        self, interaction: discord.Interaction, day: str, time: str
    ):
        """初回告知の曜日と時刻を設定する。

        Args:
            interaction: コマンドインタラクション
            day: 設定する曜日（3文字略称）
            time: 設定する時刻（HH:MM形式）
        """
        if not is_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        error = self._validate_day_time(day, time)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        self.bot.config.set(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, day
        )
        self.bot.config.set(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME, time
        )
        # スケジュールタスクを再登録
        self.bot.schedule_announce_task()

        await interaction.response.send_message(
            f"初回告知を {day} {time} に設定しました。", ephemeral=True
        )

    @config_group.command(name="event")
    @app_commands.describe(
        day="開催の曜日 (Mon, Tue, ..., Sun)",
        time="開催の時刻 (HH:MM形式)",
    )
    async def config_event(self, interaction: discord.Interaction, day: str, time: str):
        """ML集会の開催曜日と時刻を設定する（告知文面の表示に使用）。

        Args:
            interaction: コマンドインタラクション
            day: 設定する曜日（3文字略称）
            time: 設定する時刻（HH:MM形式）
        """
        if not is_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        error = self._validate_day_time(day, time)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        self.bot.config.set(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_EVENT_WEEKDAY, day
        )
        self.bot.config.set(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_EVENT_TIME, time
        )

        await interaction.response.send_message(
            f"開催日時を {day} {time} に設定しました。", ephemeral=True
        )

    @config_announce.autocomplete("day")
    @config_event.autocomplete("day")
    async def day_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """曜日選択のオートコンプリートを提供する。

        Args:
            interaction: インタラクション
            current: 現在の入力値

        Returns:
            一致する曜日の選択肢リスト
        """
        return [
            app_commands.Choice(name=day, value=day)
            for day in Weekday.ALL
            if current.lower() in day.lower()
        ]

    @config_group.command(name="role")
    @app_commands.describe(role="初回告知でメンションするロール")
    async def config_role(
        self, interaction: discord.Interaction, role: discord.Role | None = None
    ):
        """アクションロールを設定または取得する。

        Args:
            interaction: コマンドインタラクション
            role: 設定するロール、またはNoneで現在の値を取得
        """
        if role is None:
            current_role = self.bot.config.get(
                ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ACTION_ROLE, "@everyone"
            )
            await interaction.response.send_message(
                f"現在のアクションロール: {current_role}", ephemeral=True
            )
            return

        if not is_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        self.bot.config.set(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ACTION_ROLE, role.name
        )
        await interaction.response.send_message(
            f"アクションロールを {role.name} に設定しました。", ephemeral=True
        )

    config_channel = app_commands.Group(
        name="channel", description="チャンネル設定を管理", parent=config_group
    )

    @config_channel.command(name="announce")
    @app_commands.describe(channel="告知メッセージを送信するチャンネル")
    async def config_channel_announce(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
    ):
        """告知チャンネルを設定または取得する。

        Args:
            interaction: コマンドインタラクション
            channel: 設定するチャンネル、またはNoneで現在の値を取得
        """
        if channel is None:
            await interaction.response.send_message(
                f"現在の告知チャンネル: {self._announce_channel_name()}", ephemeral=True
            )
            return

        if not is_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        self.bot.config.set(
            ConfigKeys.SECTION_CHANNELS,
            ConfigKeys.KEY_ANNOUNCE_CHANNEL_ID,
            str(channel.id),
        )
        await interaction.response.send_message(
            f"告知チャンネルを {channel.name} に設定しました。", ephemeral=True
        )

    def _announce_channel_name(self) -> str:
        """設定された告知チャンネルの表示名を返す。

        Returns:
            チャンネル名。未設定なら「未設定」
        """
        channel_id = self.bot.config.get(
            ConfigKeys.SECTION_CHANNELS, ConfigKeys.KEY_ANNOUNCE_CHANNEL_ID, ""
        )
        if not channel_id:
            return "未設定"
        channel = self.bot.get_channel(int(channel_id))
        if isinstance(channel, discord.TextChannel):
            return channel.name
        return f"未知 (ID: {channel_id})"

    @config_group.command(name="show")
    async def config_show(self, interaction: discord.Interaction):
        """現在の全設定を表示する。

        Args:
            interaction: コマンドインタラクション
        """
        get = self.bot.config.get
        s = ConfigKeys.SECTION_SETTINGS
        config_info = [
            "**現在の設定:**",
            f"初回告知: {get(s, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, 'Sun')} "
            f"{get(s, ConfigKeys.KEY_ANNOUNCE_TIME, '12:00')}",
            f"開催日時: {get(s, ConfigKeys.KEY_EVENT_WEEKDAY, 'Wed')} "
            f"{get(s, ConfigKeys.KEY_EVENT_TIME, '21:30')}",
            f"アクションロール: {get(s, ConfigKeys.KEY_ACTION_ROLE, '@everyone')}",
            f"告知チャンネル: {self._announce_channel_name()}",
            f"デフォルトURL: {get(s, ConfigKeys.KEY_DEFAULT_URL, '')}",
        ]
        await interaction.response.send_message("\n".join(config_info), ephemeral=True)

    @config_group.command(name="reset")
    async def config_reset(self, interaction: discord.Interaction):
        """全設定をデフォルト値にリセットする。

        Args:
            interaction: コマンドインタラクション
        """
        if not is_admin(interaction, self.bot.config):
            await interaction.response.send_message(
                "設定をリセットする権限がありません。", ephemeral=True
            )
            return

        self.bot.config.reset()
        self.bot.schedule_announce_task()
        await interaction.response.send_message(
            "全ての設定をデフォルト値にリセットしました。", ephemeral=True
        )
        self.logger.info(f"全設定が {interaction.user} によってリセットされました")

    @config_announce.error
    @config_event.error
    @config_role.error
    @config_channel_announce.error
    @config_show.error
    @config_reset.error
    async def config_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """設定コマンドのエラーハンドラ。

        Args:
            interaction: コマンドインタラクション
            error: 発生したエラー
        """
        self.logger.error(f"設定コマンドでエラーが発生しました: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"エラーが発生しました: {error}", ephemeral=True
            )
