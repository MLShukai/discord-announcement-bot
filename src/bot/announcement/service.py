# src/bot/announcement/service.py
"""告知メッセージの生成と送信を担当するサービスモジュール。"""

import datetime
import logging
from string import Template

import discord

from ..config import ConfigManager
from ..constants import AnnouncementType, ConfigKeys, ReactionEmoji, Weekday
from .models import LTInfo


class AnnouncementService:
    """告知サービスクラス。

    告知メッセージの生成、テンプレート処理、送信を担当する。
    """

    def __init__(self, config: ConfigManager):
        """告知サービスを初期化する。

        Args:
            config: 設定マネージャー
        """
        self.logger = logging.getLogger("announce-bot.announcement")
        self.config = config
        self.lt_info = LTInfo()

    async def send_announcement(
        self,
        channel: discord.TextChannel,
        announcement_type: AnnouncementType,
        target_date: datetime.date | None = None,
    ) -> discord.Message | None:
        """告知メッセージをチャンネルに送信する。

        Args:
            channel: 送信先のDiscordチャンネル
            announcement_type: 告知の種類
            target_date: 告知対象の日付（未指定の場合は次の告知曜日）

        Returns:
            送信されたメッセージ、または送信失敗時はNone
        """
        if channel is None:
            self.logger.error("告知を送信できません: チャンネルがNoneです")
            return None

        # 告知タイプに基づいてメッセージ内容を生成
        content = self.generate_announcement_content(announcement_type, target_date)

        try:
            message = await channel.send(content)
            self.logger.info(
                f"{announcement_type} 告知を {channel.name} に送信しました"
            )

            # LT告知を送信した後はLT情報をクリア
            if announcement_type == AnnouncementType.LIGHTNING_TALK:
                self.lt_info.clear()
                self.logger.debug("LT情報をクリアしました")

            return message

        except discord.DiscordException as e:
            self.logger.error(f"告知の送信に失敗しました: {e}")
            return None

    async def send_confirmation(
        self, channel: discord.TextChannel | None, role: discord.Role | None = None
    ) -> discord.Message | None:
        """確認メッセージをチャンネルに送信し、リアクションを追加する。"""
        if channel is None:
            self.logger.error("確認メッセージを送信できません: チャンネルがNoneです")
            return None

        # 確認テンプレートを取得
        template_str = self.config.get(
            ConfigKeys.SECTION_TEMPLATES,
            ConfigKeys.KEY_TEMPLATE_CONFIRMATION,
            "$role 今度の$weekday曜日 ($month/$day) の予定を確認します。",
        )
        template = Template(template_str)

        # 次の告知日を取得
        announce_weekday = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, Weekday.SUNDAY
        )
        next_date = self.get_next_weekday(announce_weekday)

        # 曜日の日本語名を取得
        weekday_jp = Weekday.to_jp(next_date.weekday())

        # メッセージをフォーマット
        role_mention = role.mention if role else "@everyone"
        content = template.substitute(
            role=role_mention,
            weekday=weekday_jp,
            month=next_date.month,
            day=next_date.day,
        )

        # リアクション指示を追加行を削除 (テンプレートに含める)

        try:
            message = await channel.send(content)
            self.logger.info(f"確認メッセージを {channel.name} に送信しました")

            # リアクションを追加
            await message.add_reaction(ReactionEmoji.REGULAR)
            await message.add_reaction(ReactionEmoji.LIGHTNING_TALK)
            await message.add_reaction(ReactionEmoji.REST)

            return message

        except discord.DiscordException as e:
            self.logger.error(f"確認メッセージの送信に失敗しました: {e}")
            return None

    def generate_announcement_content(
        self,
        announcement_type: AnnouncementType,
        target_date: datetime.date | None = None,
    ) -> str:
        """告知タイプとテンプレートに基づいてメッセージ内容を生成する。

        Args:
            announcement_type: 告知の種類
            target_date: 告知対象の日付（未指定の場合は次の告知曜日）

        Returns:
            フォーマットされた告知メッセージ
        """
        # ターゲット日付が未指定の場合は次の告知曜日を使用
        if target_date is None:
            announce_weekday = self.config.get(
                ConfigKeys.SECTION_SETTINGS,
                ConfigKeys.KEY_ANNOUNCE_WEEKDAY,
                Weekday.SUNDAY,
            )
            target_date = self.get_next_weekday(announce_weekday)

        template_key = ""
        template_vars = {}

        # 告知タイプに基づいてテンプレートキーと変数を設定
        if announcement_type == AnnouncementType.REGULAR:
            template_key = ConfigKeys.KEY_TEMPLATE_REGULAR
            default_url = self.config.get(
                ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_DEFAULT_URL, ""
            )
            template_vars = {
                "mm": target_date.month,
                "dd": target_date.day,
                "url": default_url,
            }

        elif announcement_type == AnnouncementType.LIGHTNING_TALK:
            template_key = ConfigKeys.KEY_TEMPLATE_LIGHTNING_TALK
            default_url = self.config.get(
                ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_DEFAULT_URL, ""
            )
            template_vars = {
                "mm": target_date.month,
                "dd": target_date.day,
                "speaker_name": self.lt_info.speaker_name or "発表者未定",
                "title": self.lt_info.title or "タイトル未定",
                "url": self.lt_info.url or default_url,
            }

        elif announcement_type == AnnouncementType.REST:
            template_key = ConfigKeys.KEY_TEMPLATE_REST
            template_vars = {}  # おやすみテンプレートには変数不要

        # テンプレートを取得してフォーマット
        template_str = self.config.get(ConfigKeys.SECTION_TEMPLATES, template_key, "")
        template = Template(template_str)

        # フォーマットしたメッセージを返す
        return template.substitute(template_vars)

    def get_next_weekday(self, weekday_str: str) -> datetime.date:
        """指定された曜日の次の日付を取得する。

        Args:
            weekday_str: 3文字の曜日略称（例: 'Sun', 'Mon'）

        Returns:
            次の該当曜日の日付
        """
        target_weekday = Weekday.to_int(weekday_str)
        today = datetime.date.today()
        days_ahead = target_weekday - today.weekday()

        # 当日または今週の対象曜日が過ぎた場合は次週を見る
        if days_ahead <= 0:
            days_ahead += 7

        return today + datetime.timedelta(days=days_ahead)

    @property
    def lt_speaker(self) -> str | None:
        """LT発表者名を取得する。

        Returns:
            LT発表者名、未設定の場合はNone
        """
        return self.lt_info.speaker_name

    @lt_speaker.setter
    def lt_speaker(self, name: str | None) -> None:
        """LT発表者名を設定する。

        Args:
            name: 設定する発表者名
        """
        self.lt_info.speaker_name = name
        self.logger.info(f"LT発表者を設定しました: {name}")

    @property
    def lt_title(self) -> str | None:
        """LTタイトルを取得する。

        Returns:
            LTタイトル、未設定の場合はNone
        """
        return self.lt_info.title

    @lt_title.setter
    def lt_title(self, title: str | None) -> None:
        """LTタイトルを設定する。

        Args:
            title: 設定するタイトル
        """
        self.lt_info.title = title
        self.logger.info(f"LTタイトルを設定しました: {title}")

    @property
    def lt_url(self) -> str | None:
        """LT URLを取得する。

        Returns:
            LT URL、未設定の場合はNone
        """
        return self.lt_info.url

    @lt_url.setter
    def lt_url(self, url: str | None) -> None:
        """LT URLを設定する。

        Args:
            url: 設定するURL
        """
        self.lt_info.url = url
        self.logger.info(f"LT URLを設定しました: {url}")
