# src/bot/commands/utility_cog.py
"""Botの状態表示とヘルプ、テスト機能を提供するコマンドモジュール。"""

import datetime
import logging

import discord
from discord import app_commands
from discord.ext import commands

from ..client import AnnounceBotClient
from ..constants import AnnouncementType, ConfigKeys, Weekday


class UtilityCog(commands.Cog):
    """ユーティリティコマンドを提供するコグ。

    状態表示、ヘルプ、テストコマンドを提供する。
    """

    def __init__(self, bot: AnnounceBotClient):
        """ユーティリティコマンドコグを初期化する。

        Args:
            bot: Botクライアントインスタンス
        """
        self.bot = bot
        self.logger = logging.getLogger("announce-bot.commands.utility")

    def _check_admin_permissions(self, interaction: discord.Interaction) -> bool:
        """ユーザーが管理者権限を持っているか確認する。

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

    @app_commands.command(name="status")
    async def status(self, interaction: discord.Interaction):
        """Botの現在の状態とスケジュールされたイベントを表示する。

        Args:
            interaction: コマンドインタラクション
        """
        # 次の確認日時を取得
        confirm_time = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_TIME, "21:30"
        )
        confirm_weekday = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_WEEKDAY, "Thu"
        )

        # 次の告知日時を取得
        announce_time = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME, "21:30"
        )
        announce_weekday = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, "Sun"
        )

        # 次の日付を計算
        today = datetime.date.today()

        # 次の確認日
        confirm_day = Weekday.to_int(confirm_weekday)
        days_to_confirm = (confirm_day - today.weekday()) % 7
        if days_to_confirm == 0:  # 当日の場合
            hour, minute = map(int, confirm_time.split(":"))
            now = datetime.datetime.now()
            if now.hour > hour or (now.hour == hour and now.minute >= minute):
                days_to_confirm = 7  # 次週

        next_confirm = today + datetime.timedelta(days=days_to_confirm)

        # 次の告知日
        announce_day = Weekday.to_int(announce_weekday)
        days_to_announce = (announce_day - today.weekday()) % 7
        if days_to_announce == 0:  # 当日の場合
            hour, minute = map(int, announce_time.split(":"))
            now = datetime.datetime.now()
            if now.hour > hour or (now.hour == hour and now.minute >= minute):
                days_to_announce = 7  # 次週

        next_announce = today + datetime.timedelta(days=days_to_announce)

        # 日付をフォーマット
        confirm_jp_day = Weekday.to_jp(next_confirm.weekday())
        announce_jp_day = Weekday.to_jp(next_announce.weekday())

        # ステータスメッセージを構築
        status_parts = [
            "**ボットステータス:**",
            f"次回確認: {next_confirm.month}/{next_confirm.day} ({confirm_jp_day}) {confirm_time}",
            f"次回告知: {next_announce.month}/{next_announce.day} ({announce_jp_day}) {announce_time}",
            f"告知タイプ: {self.bot.next_announcement_type}",
        ]

        # LT情報があれば追加
        lt_info = self.bot.announcement_service.lt_info
        if any([lt_info.speaker_name, lt_info.title, lt_info.url]):
            status_parts.append("\n**LT情報:**")
            if lt_info.speaker_name is not None:
                status_parts.append(f"発表者: {lt_info.speaker_name}")
            if lt_info.title is not None:
                status_parts.append(f"タイトル: {lt_info.title}")
            if lt_info.url is not None:
                status_parts.append(f"URL: {lt_info.url}")

            # 完全性ステータスを追加
            is_complete = lt_info.is_complete
            status = "✅ 完全" if is_complete else "⚠️ 不完全"
            status_parts.append(f"ステータス: {status}")

        await interaction.response.send_message("\n".join(status_parts), ephemeral=True)

    @app_commands.command(name="help")
    @app_commands.describe(command="ヘルプを表示するコマンド名")
    async def help_command(
        self, interaction: discord.Interaction, command: str | None = None
    ):
        """Botコマンドのヘルプ情報を表示する。

        Args:
            interaction: コマンドインタラクション
            command: ヘルプを表示する特定のコマンド、またはNone全般的なヘルプ
        """
        if command is None:
            # 一般ヘルプ
            help_text = [
                "**DiscordアナウンスBot - コマンドヘルプ**",
                "",
                "**LT管理コマンド:**",
                "`/lt speaker [name]` - 発表者を設定/表示",
                "`/lt title [title]` - タイトルを設定/表示",
                "`/lt url [url]` - URLを設定/表示",
                "`/lt info` - 現在のLT情報を表示",
                "`/lt clear` - LT情報をクリア",
                "",
                "**設定コマンド:**",
                "`/config time confirm [time]` - 確認時刻を設定/表示",
                "`/config time announce [time]` - 告知時刻を設定/表示",
                "`/config weekday confirm [day]` - 確認曜日を設定/表示",
                "`/config weekday announce [day]` - 告知曜日を設定/表示",
                "`/config role [role]` - アクションロールを設定/表示",
                "`/config channel action [channel]` - アクションチャンネルを設定/表示",
                "`/config channel announce [channel]` - 告知チャンネルを設定/表示",
                "`/config show` - 現在の設定をすべて表示",
                "`/config reset` - 設定をデフォルト値にリセット",
                "",
                "**ユーティリティコマンド:**",
                "`/status` - ボットの状態と次回イベントを表示",
                "`/help [command]` - ヘルプを表示",
                "",
                "**テストコマンド:**",
                "`/test announce` - 告知メッセージのプレビュー",
                "`/test confirm` - 確認メッセージのプレビュー",
                "",
                "**手動実行コマンド:**",
                "`/manual confirm` - 確認メッセージを手動送信",
                "`/manual announce` - 告知メッセージを手動送信",
                "",
                "特定のコマンドの詳細については `/help [command]` を使用してください。",
            ]

            await interaction.response.send_message(
                "\n".join(help_text), ephemeral=True
            )

        else:
            # コマンド固有のヘルプ
            command = command.lower()

            if command == "lt" or command.startswith("lt "):
                help_text = [
                    "**LT管理コマンド**",
                    "",
                    "`/lt speaker [name]` - 発表者名を設定または取得します。名前を指定しない場合は現在の設定を表示します。",
                    "`/lt title [title]` - 発表タイトルを設定または取得します。タイトルを指定しない場合は現在の設定を表示します。",
                    "`/lt url [url]` - イベントのURLを設定または取得します。URLを指定しない場合は現在の設定を表示します。",
                    "`/lt info` - 現在設定されているLT情報をすべて表示します。",
                    "`/lt clear` - LT情報をすべてクリアします。",
                    "",
                    "**権限:** これらのコマンドは 'LT管理者'、'Moderator'、または 'Administrator' ロールを持つユーザーのみが実行できます。",
                ]

            elif command == "config" or command.startswith("config "):
                help_text = [
                    "**設定管理コマンド**",
                    "",
                    "**時間設定:**",
                    "`/config time confirm [time]` - 確認メッセージの時刻を設定または取得します。時刻はHH:MM形式です。",
                    "`/config time announce [time]` - 告知メッセージの時刻を設定または取得します。時刻はHH:MM形式です。",
                    "",
                    "**曜日設定:**",
                    "`/config weekday confirm [day]` - 確認メッセージの曜日を設定または取得します。曜日は3文字の英語略称（Mon, Tue, ...）です。",
                    "`/config weekday announce [day]` - 告知メッセージの曜日を設定または取得します。曜日は3文字の英語略称（Mon, Tue, ...）です。",
                    "",
                    "**ロール設定:**",
                    "`/config role [role]` - アクションロールを設定または取得します。",
                    "",
                    "**チャンネル設定:**",
                    "`/config channel action [channel]` - アクションチャンネルを設定または取得します。",
                    "`/config channel announce [channel]` - 告知チャンネルを設定または取得します。",
                    "",
                    "`/config show` - 現在の全設定を表示します。",
                    "`/config reset` - 設定をデフォルト値にリセットします。",
                    "",
                    "**権限:** これらのコマンドは 'Moderator' または 'Administrator' ロールを持つユーザーのみが実行できます。",
                ]

            elif command == "status":
                help_text = [
                    "**ステータスコマンド**",
                    "",
                    "`/status` - 次回の確認イベントと告知イベントの日時、および現在のLT情報を表示します。",
                    "",
                    "誰でも実行できます。",
                ]

            elif command == "test" or command.startswith("test "):
                help_text = [
                    "**テストコマンド**",
                    "",
                    "`/test announce` - 告知メッセージのプレビューを表示します。実際には投稿されません。",
                    "`/test confirm` - 確認メッセージのプレビューを表示します。実際には投稿されません。",
                    "",
                    "**権限:** これらのコマンドは 'Moderator' または 'Administrator' ロールを持つユーザーのみが実行できます。",
                ]

            elif command == "manual" or command.startswith("manual "):
                help_text = [
                    "**手動実行コマンド**",
                    "",
                    "`/manual confirm` - 手動で確認メッセージを送信します。",
                    "`/manual announce` - 手動で告知メッセージを送信します。",
                    "",
                    "**権限:** これらのコマンドは 'Moderator' または 'Administrator' ロールを持つユーザーのみが実行できます。",
                ]

            else:
                help_text = [
                    f"コマンド '{command}' に関するヘルプは見つかりませんでした。\n`/help` を使用して全コマンドの一覧を確認してください。"
                ]

            await interaction.response.send_message(
                "\n".join(help_text), ephemeral=True
            )

    # テストコマンドグループ
    test_group = app_commands.Group(name="test", description="テスト用コマンド")

    @test_group.command(name="announce")
    @app_commands.describe(type="アナウンスの種類")
    async def test_announce(
        self, interaction: discord.Interaction, type: str = "regular"
    ):
        """告知メッセージをプレビューする（実際には送信しない）。

        Args:
            interaction: コマンドインタラクション
            type: テストする告知の種類（regular, lt, rest）
        """
        # 権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
            return

        type_map: dict[str, AnnouncementType] = {
            "regular": AnnouncementType.REGULAR,
            "lt": AnnouncementType.LIGHTNING_TALK,
            "rest": AnnouncementType.REST,
        }

        announcement_type = type_map.get(type.lower(), AnnouncementType.REGULAR)

        # メッセージを生成
        message = self.bot.announcement_service.generate_announcement_content(
            announcement_type
        )

        await interaction.response.send_message(
            f"**告知メッセージプレビュー ({type}):**\n\n{message}", ephemeral=True
        )

    @test_announce.autocomplete("type")
    async def test_announce_autocomplete(
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

    @test_group.command(name="confirm")
    async def test_confirm(self, interaction: discord.Interaction):
        """確認メッセージをプレビューする（実際には送信しない）。

        Args:
            interaction: コマンドインタラクション
        """
        # 権限チェック
        if not self._check_admin_permissions(interaction):
            await interaction.response.send_message(
                "このコマンドを実行する権限がありません。", ephemeral=True
            )
            return

        # 確認テンプレートを取得
        template_str = self.bot.config.get(
            ConfigKeys.SECTION_TEMPLATES,
            ConfigKeys.KEY_TEMPLATE_CONFIRMATION,
            "$role 今度の日曜 ($month/$day) の予定を確認します。",
        )

        # 次の告知日を取得
        announce_weekday = self.bot.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, "Sun"
        )
        next_date = self.bot.announcement_service.get_next_weekday(announce_weekday)

        # メッセージをフォーマット
        import string

        template = string.Template(template_str)

        content = template.substitute(
            role="@Role", month=next_date.month, day=next_date.day
        )

        # リアクション指示を追加
        content += "\n👍: 通常開催\n⚡: LT開催\n💤: おやすみ\nリアクションがない場合は通常開催として扱います。"

        await interaction.response.send_message(
            f"**確認メッセージプレビュー:**\n\n{content}", ephemeral=True
        )

    @status.error
    @help_command.error
    @test_announce.error
    @test_confirm.error
    async def utility_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """ユーティリティコマンドのエラーハンドラ。

        Args:
            interaction: コマンドインタラクション
            error: 発生したエラー
        """
        self.logger.error(f"ユーティリティコマンドでエラーが発生しました: {error}")
        await interaction.response.send_message(
            f"エラーが発生しました: {error}", ephemeral=True
        )
