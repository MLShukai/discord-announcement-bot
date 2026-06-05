# src/bot/announcement/service.py
"""告知メッセージの生成と送信を担当するサービスモジュール。"""

import datetime
import logging
from string import Template

import discord

from ..clock import Clock, SystemClock
from ..config import ConfigManager
from ..constants import AnnouncementType, ConfigKeys, ReactionEmoji, Weekday
from ..state import StateStore

# 初回告知メッセージ末尾に付与するリアクション凡例
REACTION_LEGEND = (
    "\n\n――― 今週の予定を変更する場合は下のリアクションを押してください ―――\n"
    f"{ReactionEmoji.REGULAR}: 通常開催  "
    f"{ReactionEmoji.LIGHTNING_TALK}: LT開催  "
    f"{ReactionEmoji.WORKSPACE}: 作業部屋開催  "
    f"{ReactionEmoji.REST}: おやすみ"
)


class AnnouncementService:
    """告知サービスクラス。

    初回告知・開催告知のメッセージ生成とDiscordへの送信を担当する。
    """

    def __init__(
        self,
        config: ConfigManager,
        state: StateStore,
        clock: Clock | None = None,
    ):
        """告知サービスを初期化する。

        Args:
            config: 設定マネージャー
            state: 実行時状態ストア
            clock: 時刻ソース（未指定なら `SystemClock`）
        """
        self.logger = logging.getLogger("announce-bot.announcement")
        self.config = config
        self.state = state
        self.clock = clock or SystemClock()

    def next_event_date(self) -> datetime.date:
        """次の開催日（設定された開催曜日）の日付を返す。

        Returns:
            次の開催曜日の日付
        """
        event_weekday = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_EVENT_WEEKDAY, Weekday.WEDNESDAY
        )
        return self._next_weekday(event_weekday)

    def _next_weekday(self, weekday_str: str) -> datetime.date:
        """指定曜日の次の日付を返す（当日を含まず最短の未来日）。

        Args:
            weekday_str: 3文字の曜日略称（例: 'Wed'）

        Returns:
            次の該当曜日の日付
        """
        target_weekday = Weekday.to_int(weekday_str)
        today = self.clock.today()
        days_ahead = target_weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + datetime.timedelta(days=days_ahead)

    def _template_vars(self, target_date: datetime.date) -> dict[str, object]:
        """テンプレート展開に使う共通変数を組み立てる。

        Args:
            target_date: 開催日

        Returns:
            `string.Template` へ渡す変数辞書
        """
        default_url = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_DEFAULT_URL, ""
        )
        event_time = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_EVENT_TIME, "21:30"
        )
        lt = self.state.state.lt
        return {
            "month": target_date.month,
            "day": target_date.day,
            "weekday": Weekday.to_jp(target_date.weekday()),
            "time": event_time,
            "url": lt.url or default_url,
            "speaker_name": lt.speaker_name or "発表者未定",
            "title": lt.title or "タイトル未定",
        }

    def build_announce(self, announcement_type: AnnouncementType) -> str:
        """初回告知メッセージ（リアクション凡例付き）を生成する。

        Args:
            announcement_type: 今週の開催種別

        Returns:
            送信用のメッセージ本文
        """
        template_key = ConfigKeys.ANNOUNCE_TEMPLATE_KEYS[announcement_type]
        template_str = self.config.get(ConfigKeys.SECTION_TEMPLATES, template_key, "")
        content = Template(template_str).safe_substitute(
            self._template_vars(self.next_event_date())
        )
        return content + REACTION_LEGEND

    def build_open(self, announcement_type: AnnouncementType) -> str | None:
        """開催告知メッセージを生成する。

        Args:
            announcement_type: 今週の開催種別

        Returns:
            送信用のメッセージ本文。おやすみ（REST）の場合は None
        """
        template_key = ConfigKeys.OPEN_TEMPLATE_KEYS.get(announcement_type)
        if template_key is None:
            return None
        template_str = self.config.get(ConfigKeys.SECTION_TEMPLATES, template_key, "")
        return Template(template_str).safe_substitute(
            self._template_vars(self.next_event_date())
        )

    async def send_announce(
        self, channel: discord.TextChannel | None
    ) -> discord.Message | None:
        """初回告知を送信し、リアクションを付与して状態を更新する。

        Args:
            channel: 送信先の告知チャンネル

        Returns:
            送信されたメッセージ、または送信失敗時は None
        """
        if channel is None:
            self.logger.error("初回告知を送信できません: チャンネルがNoneです")
            return None

        session_type = self.state.state.session_type
        content = self.build_announce(session_type)
        try:
            message = await channel.send(content)
            self.logger.info(
                f"初回告知({session_type})を {channel.name} に送信しました"
            )

            for emoji in (
                ReactionEmoji.REGULAR,
                ReactionEmoji.LIGHTNING_TALK,
                ReactionEmoji.WORKSPACE,
                ReactionEmoji.REST,
            ):
                await message.add_reaction(emoji)

            # 選択対象メッセージとして記録し永続化
            self.state.state.announce_message_id = message.id
            self.state.state.target_event_date = self.next_event_date()
            self.state.save()
            return message
        except discord.DiscordException as e:
            self.logger.error(f"初回告知の送信に失敗しました: {e}")
            return None

    async def send_open(
        self, channel: discord.TextChannel | None
    ) -> discord.Message | None:
        """開催告知を送信する。

        おやすみ（REST）の週は送信しない（None を返す）。

        Args:
            channel: 送信先の告知チャンネル

        Returns:
            送信されたメッセージ。REST または送信失敗時は None
        """
        if channel is None:
            self.logger.error("開催告知を送信できません: チャンネルがNoneです")
            return None

        session_type = self.state.state.session_type
        content = self.build_open(session_type)
        if content is None:
            return None

        try:
            message = await channel.send(content)
            self.logger.info(
                f"開催告知({session_type})を {channel.name} に送信しました"
            )
            return message
        except discord.DiscordException as e:
            self.logger.error(f"開催告知の送信に失敗しました: {e}")
            return None
