# src/bot/commands/config_cog.py
"""Bot設定管理のためのコマンドモジュール。"""

import logging
import re

import discord
from discord import app_commands
from discord.ext import commands

from ..client import AnnounceBotClient
from ..constants import ConfigKeys, Weekday


class ConfigCog(commands.Cog):
    """Bot設定を管理するためのコマンドコグ。

    時間、曜日、チャンネル、ロールなどの設定管理機能を提供する。
    """

    def __init__(self, bot: AnnounceBotClient):
        """設定コマンドコグを初期化する。

        Args:
            bot: Botクライアントインスタンス
        """
        self.bot = bot
        self.logger = logging.getLogger("announce-bot.commands.config")

    def _check_admin_permissions(self, interaction: discord.Interaction) -> bool:
        """ユーザーがBot設定を管理する権限を持っているか確認する。

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

    config_group = app_commands.Group(name="config", description="ボットの設定を管理")

    # 時間設定
    config_time = app_commands.Group(
        name="time", description="時間設定を管理", parent=config_group
    )

    @config_time.command(name="confirm")
    @app_commands.describe(time="確認メッセージの時間 (HH:MM形式)")
    async def config_time_confirm(
        self, interaction: discord.Interaction, time: str | None = None
    ):
        """確認メッセージの時刻を設定または取得する。

        Args:
            interaction: コマンドインタラクション
            time: 設定する時刻（HH:MM形式）、またはNoneで現在の値を取得
        """
        # 現在の値を取得する場合
        if time is None:
            current_time = self.bot.config.get(
                ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_TIME, "21:30"
            )
            await interaction.response.send_message(
                f"現在の確認時刻: {current_time}", ephemeral=True
            )
            return

        # 設定時は権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        # 時間形式バリデーション
        if not re.match(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$", time):
            await interaction.response.send_message(
                "無効な時間形式です。HH:MM形式で入力してください。", ephemeral=True
            )
            return

        # 設定を更新
        self.bot.config.set(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_TIME, time
        )

        # スケジュールタスクを更新
        confirm_weekday = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_WEEKDAY, "Thu"
        )
        self.bot.scheduler.schedule_daily_task(
            "confirmation", time, confirm_weekday, self.bot.confirmation_task
        )

        await interaction.response.send_message(
            f"確認時刻を {time} に設定しました。", ephemeral=True
        )

    @config_time.command(name="announce")
    @app_commands.describe(time="告知メッセージの時間 (HH:MM形式)")
    async def config_time_announce(
        self, interaction: discord.Interaction, time: str | None = None
    ):
        """告知メッセージの時刻を設定または取得する。

        Args:
            interaction: コマンドインタラクション
            time: 設定する時刻（HH:MM形式）、またはNoneで現在の値を取得
        """
        # 現在の値を取得する場合
        if time is None:
            current_time = self.bot.config.get(
                ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME, "21:30"
            )
            await interaction.response.send_message(
                f"現在の告知時刻: {current_time}", ephemeral=True
            )
            return

        # 設定時は権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        # 時間形式バリデーション
        if not re.match(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$", time):
            await interaction.response.send_message(
                "無効な時間形式です。HH:MM形式で入力してください。", ephemeral=True
            )
            return

        # 設定を更新
        self.bot.config.set(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME, time
        )

        # スケジュールタスクを更新
        announce_weekday = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, "Sun"
        )
        self.bot.scheduler.schedule_daily_task(
            "announcement", time, announce_weekday, self.bot.announcement_task
        )

        await interaction.response.send_message(
            f"告知時刻を {time} に設定しました。", ephemeral=True
        )

    # 曜日設定
    config_weekday = app_commands.Group(
        name="weekday", description="曜日設定を管理", parent=config_group
    )

    @config_weekday.command(name="confirm")
    @app_commands.describe(day="確認メッセージの曜日 (3文字の英語略称)")
    async def config_weekday_confirm(
        self, interaction: discord.Interaction, day: str | None = None
    ):
        """確認メッセージの曜日を設定または取得する。

        Args:
            interaction: コマンドインタラクション
            day: 設定する曜日（3文字略称）、またはNoneで現在の値を取得
        """
        # 現在の値を取得する場合
        if day is None:
            current_day = self.bot.config.get(
                ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_WEEKDAY, "Thu"
            )
            await interaction.response.send_message(
                f"現在の確認曜日: {current_day}", ephemeral=True
            )
            return

        # 設定時は権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        # 曜日形式バリデーション
        valid_weekdays = [
            Weekday.MONDAY,
            Weekday.TUESDAY,
            Weekday.WEDNESDAY,
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY,
        ]
        if day not in valid_weekdays:
            await interaction.response.send_message(
                f"無効な曜日形式です。有効な値: {', '.join(valid_weekdays)}",
                ephemeral=True,
            )
            return

        # 設定を更新
        self.bot.config.set(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_WEEKDAY, day
        )

        # スケジュールタスクを更新
        confirm_time = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_TIME, "21:30"
        )
        self.bot.scheduler.schedule_daily_task(
            "confirmation", confirm_time, day, self.bot.confirmation_task
        )

        await interaction.response.send_message(
            f"確認曜日を {day} に設定しました。", ephemeral=True
        )

    @config_weekday_confirm.autocomplete("day")
    async def weekday_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """曜日選択のオートコンプリートを提供する。

        Args:
            interaction: インタラクション
            current: 現在の入力値

        Returns:
            一致する曜日の選択肢リスト
        """
        weekdays = [
            Weekday.MONDAY,
            Weekday.TUESDAY,
            Weekday.WEDNESDAY,
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY,
        ]
        return [
            app_commands.Choice(name=day, value=day)
            for day in weekdays
            if current.lower() in day.lower()
        ]

    @config_weekday.command(name="announce")
    @app_commands.describe(day="告知メッセージの曜日 (3文字の英語略称)")
    async def config_weekday_announce(
        self, interaction: discord.Interaction, day: str | None = None
    ):
        """告知メッセージの曜日を設定または取得する。

        Args:
            interaction: コマンドインタラクション
            day: 設定する曜日（3文字略称）、またはNoneで現在の値を取得
        """
        # 現在の値を取得する場合
        if day is None:
            current_day = self.bot.config.get(
                ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, "Sun"
            )
            await interaction.response.send_message(
                f"現在の告知曜日: {current_day}", ephemeral=True
            )
            return

        # 設定時は権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        # 曜日形式バリデーション
        valid_weekdays = [
            Weekday.MONDAY,
            Weekday.TUESDAY,
            Weekday.WEDNESDAY,
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY,
        ]
        if day not in valid_weekdays:
            await interaction.response.send_message(
                f"無効な曜日形式です。有効な値: {', '.join(valid_weekdays)}",
                ephemeral=True,
            )
            return

        # 設定を更新
        self.bot.config.set(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, day
        )

        # スケジュールタスクを更新
        announce_time = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME, "21:30"
        )
        self.bot.scheduler.schedule_daily_task(
            "announcement", announce_time, day, self.bot.announcement_task
        )

        await interaction.response.send_message(
            f"告知曜日を {day} に設定しました。", ephemeral=True
        )

    @config_weekday_announce.autocomplete("day")
    async def weekday_announce_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """曜日選択のオートコンプリートを提供する。

        Args:
            interaction: インタラクション
            current: 現在の入力値

        Returns:
            一致する曜日の選択肢リスト
        """
        weekdays = [
            Weekday.MONDAY,
            Weekday.TUESDAY,
            Weekday.WEDNESDAY,
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY,
        ]
        return [
            app_commands.Choice(name=day, value=day)
            for day in weekdays
            if current.lower() in day.lower()
        ]

    # ロール設定
    @config_group.command(name="role")
    @app_commands.describe(role="アクションに使用するロール")
    async def config_role(
        self, interaction: discord.Interaction, role: discord.Role | None = None
    ):
        """アクションロールを設定または取得する。

        Args:
            interaction: コマンドインタラクション
            role: 設定するロール、またはNoneで現在の値を取得
        """
        # 現在の値を取得する場合
        if role is None:
            current_role = self.bot.config.get(
                ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ACTION_ROLE, "@everyone"
            )
            await interaction.response.send_message(
                f"現在のアクションロール: {current_role}", ephemeral=True
            )
            return

        # 設定時は権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        # 設定を更新
        self.bot.config.set(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ACTION_ROLE, role.name
        )

        await interaction.response.send_message(
            f"アクションロールを {role.name} に設定しました。", ephemeral=True
        )

    # チャンネル設定
    config_channel = app_commands.Group(
        name="channel", description="チャンネル設定を管理", parent=config_group
    )

    @config_channel.command(name="action")
    @app_commands.describe(channel="確認メッセージを送信するチャンネル")
    async def config_channel_action(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
    ):
        """アクションチャンネルを設定または取得する。

        Args:
            interaction: コマンドインタラクション
            channel: 設定するチャンネル、またはNoneで現在の値を取得
        """
        # 現在の値を取得する場合
        if channel is None:
            current_channel_id = self.bot.config.get(
                ConfigKeys.SECTION_CHANNELS, ConfigKeys.KEY_ACTION_CHANNEL_ID, ""
            )

            if current_channel_id:
                current_channel = self.bot.get_channel(int(current_channel_id))
                if not isinstance(current_channel, discord.TextChannel):
                    return
                channel_name = (
                    current_channel.name
                    if current_channel
                    else f"未知 (ID: {current_channel_id})"
                )  # type: ignore
            else:
                channel_name = "未設定"

            await interaction.response.send_message(
                f"現在のアクションチャンネル: {channel_name}", ephemeral=True
            )
            return

        # 設定時は権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        # 設定を更新
        self.bot.config.set(
            ConfigKeys.SECTION_CHANNELS,
            ConfigKeys.KEY_ACTION_CHANNEL_ID,
            str(channel.id),
        )

        await interaction.response.send_message(
            f"アクションチャンネルを {channel.name} に設定しました。", ephemeral=True
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
        # 現在の値を取得する場合
        if channel is None:
            current_channel_id = self.bot.config.get(
                ConfigKeys.SECTION_CHANNELS, ConfigKeys.KEY_ANNOUNCE_CHANNEL_ID, ""
            )

            if current_channel_id:
                current_channel = self.bot.get_channel(int(current_channel_id))
                if not isinstance(current_channel, discord.TextChannel):
                    return
                channel_name = (
                    current_channel.name
                    if current_channel
                    else f"未知 (ID: {current_channel_id})"
                )  # type: ignore
            else:
                channel_name = "未設定"

            await interaction.response.send_message(
                f"現在の告知チャンネル: {channel_name}", ephemeral=True
            )
            return

        # 設定時は権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "設定を変更する権限がありません。", ephemeral=True
            )
            return

        # 設定を更新
        self.bot.config.set(
            ConfigKeys.SECTION_CHANNELS,
            ConfigKeys.KEY_ANNOUNCE_CHANNEL_ID,
            str(channel.id),
        )

        await interaction.response.send_message(
            f"告知チャンネルを {channel.name} に設定しました。", ephemeral=True
        )

    # 全設定表示
    @config_group.command(name="show")
    async def config_show(self, interaction: discord.Interaction):
        """現在の全設定を表示する。

        Args:
            interaction: コマンドインタラクション
        """
        # 設定情報メッセージを構築
        config_info: list[str] = []

        # 時間設定
        confirm_time = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_TIME, "21:30"
        )
        announce_time = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME, "21:30"
        )
        config_info.append(f"確認時刻: {confirm_time}")
        config_info.append(f"告知時刻: {announce_time}")

        # 曜日設定
        confirm_weekday = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_WEEKDAY, "Thu"
        )
        announce_weekday = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, "Sun"
        )
        config_info.append(f"確認曜日: {confirm_weekday}")
        config_info.append(f"告知曜日: {announce_weekday}")

        # ロール設定
        action_role = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ACTION_ROLE, "@everyone"
        )
        config_info.append(f"アクションロール: {action_role}")

        # チャンネル設定
        action_channel_id = self.bot.config.get(
            ConfigKeys.SECTION_CHANNELS, ConfigKeys.KEY_ACTION_CHANNEL_ID, ""
        )
        announce_channel_id = self.bot.config.get(
            ConfigKeys.SECTION_CHANNELS, ConfigKeys.KEY_ANNOUNCE_CHANNEL_ID, ""
        )

        if action_channel_id:
            action_channel = self.bot.get_channel(int(action_channel_id))
            if not isinstance(action_channel, discord.TextChannel):
                self.logger.error(
                    "アクションチャネルがテキストチャネルではありません。"
                )
                return
            action_channel_name = (
                action_channel.name
                if action_channel
                else f"未知 (ID: {action_channel_id})"
            )  # type: ignore
        else:
            action_channel_name = "未設定"

        if announce_channel_id:
            announce_channel = self.bot.get_channel(int(announce_channel_id))
            if not isinstance(announce_channel, discord.TextChannel):
                self.logger.error("告知チャネルがテキストチャネルではありません。")
                return
            announce_channel_name = (
                announce_channel.name
                if announce_channel
                else f"未知 (ID: {announce_channel_id})"
            )  # type: ignore
        else:
            announce_channel_name = "未設定"

        config_info.append(f"アクションチャンネル: {action_channel_name}")
        config_info.append(f"告知チャンネル: {announce_channel_name}")

        # URL設定
        default_url = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_DEFAULT_URL, ""
        )
        config_info.append(f"デフォルトURL: {default_url}")

        await interaction.response.send_message(
            "**現在の設定:**\n" + "\n".join(config_info), ephemeral=True
        )

    # 全設定リセット
    @config_group.command(name="reset")
    async def config_reset(self, interaction: discord.Interaction):
        """全設定をデフォルト値にリセットする。

        Args:
            interaction: コマンドインタラクション
        """
        # 権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "設定をリセットする権限がありません。", ephemeral=True
            )
            return

        # 設定をリセット
        self.bot.config.reset()

        # デフォルト値でスケジュールタスクをリセット
        confirm_time = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_TIME, "21:30"
        )
        confirm_weekday = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_WEEKDAY, "Thu"
        )
        announce_time = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME, "21:30"
        )
        announce_weekday = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, "Sun"
        )

        self.bot.scheduler.schedule_daily_task(
            "confirmation", confirm_time, confirm_weekday, self.bot.confirmation_task
        )

        self.bot.scheduler.schedule_daily_task(
            "announcement", announce_time, announce_weekday, self.bot.announcement_task
        )

        await interaction.response.send_message(
            "全ての設定をデフォルト値にリセットしました。", ephemeral=True
        )
        self.logger.info(f"全設定が {interaction.user} によってリセットされました")

    @config_time_confirm.error
    @config_time_announce.error
    @config_weekday_confirm.error
    @config_weekday_announce.error
    @config_role.error
    @config_channel_action.error
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
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
        else:
            self.logger.error(f"設定コマンドでエラーが発生しました: {error}")
            await interaction.response.send_message(
                f"エラーが発生しました: {error}", ephemeral=True
            )
