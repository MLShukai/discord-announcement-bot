# src/bot/constants.py
"""Bot共通の定数を定義するモジュール。"""

from enum import Enum, auto
from typing import override


# リアクション絵文字
class ReactionEmoji:
    """確認メッセージに使用するリアクション絵文字。"""

    REGULAR = "👍"  # 通常開催
    LIGHTNING_TALK = "⚡"  # LT開催
    REST = "💤"  # おやすみ


# 曜日定数
class Weekday:
    """曜日の文字列表現。"""

    MONDAY = "Mon"
    TUESDAY = "Tue"
    WEDNESDAY = "Wed"
    THURSDAY = "Thu"
    FRIDAY = "Fri"
    SATURDAY = "Sat"
    SUNDAY = "Sun"

    # 曜日対応マップ（文字列→数値）
    MAP_TO_INT = {
        MONDAY: 0,
        TUESDAY: 1,
        WEDNESDAY: 2,
        THURSDAY: 3,
        FRIDAY: 4,
        SATURDAY: 5,
        SUNDAY: 6,
    }

    # 曜日対応マップ（日本語）
    JP_WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

    @classmethod
    def to_int(cls, weekday_str: str) -> int:
        """文字列の曜日を数値に変換。

        Args:
            weekday_str: 変換する曜日の文字列

        Returns:
            曜日の数値表現（0-6、月-日）
        """
        return cls.MAP_TO_INT.get(weekday_str, 6)  # デフォルトは日曜日

    @classmethod
    def to_jp(cls, weekday_int: int) -> str:
        """数値の曜日を日本語表記に変換。

        Args:
            weekday_int: 変換する曜日の数値（0-6、月-日）

        Returns:
            曜日の日本語表記
        """
        return cls.JP_WEEKDAYS[weekday_int % 7]


# 環境変数のキー
class EnvKeys:
    """環境変数のキー定数。"""

    DISCORD_TOKEN = "DISCORD_TOKEN"
    LOG_DIR = "LOG_DIR"
    ADMIN_ROLE = "ADMIN_ROLE"
    MODERATOR_ROLE = "MODERATOR_ROLE"
    LT_ADMIN_ROLE = "LT_ADMIN_ROLE"
    CONFIG_PATH = "CONFIG_PATH"
    CONFIG_OVERRIDES_PATH = "CONFIG_OVERRIDES_PATH"


# 設定ファイルのセクションとキー
class ConfigKeys:
    """設定ファイルのセクションとキー。"""

    # セクション
    SECTION_SETTINGS = "settings"
    SECTION_CHANNELS = "channels"
    SECTION_PERMISSIONS = "permissions"
    SECTION_TEMPLATES = "templates"

    # 設定キー
    KEY_ANNOUNCE_TIME = "announce_time"
    KEY_CONFIRM_TIME = "confirm_time"
    KEY_ACTION_ROLE = "action_role"
    KEY_CONFIRM_WEEKDAY = "confirm_weekday"
    KEY_ANNOUNCE_WEEKDAY = "announce_weekday"
    KEY_DEFAULT_URL = "default_url"

    # チャンネルキー
    KEY_ACTION_CHANNEL_ID = "action_channel_id"
    KEY_ANNOUNCE_CHANNEL_ID = "announce_channel_id"

    # 権限キー
    KEY_ADMIN_ROLES = "admin_roles"
    KEY_MODERATOR_ROLES = "moderator_roles"
    KEY_LT_ADMIN_ROLES = "lt_admin_roles"

    # テンプレートキー
    KEY_TEMPLATE_REGULAR = "regular"
    KEY_TEMPLATE_LIGHTNING_TALK = "lightning_talk"
    KEY_TEMPLATE_REST = "rest"
    KEY_TEMPLATE_CONFIRMATION = "confirmation"


# アナウンスメントタイプ
class AnnouncementType(Enum):
    """告知の種類を定義する列挙型。"""

    REGULAR = auto()  # 通常開催
    LIGHTNING_TALK = auto()  # LT開催
    REST = auto()  # おやすみ

    @override
    def __str__(self) -> str:
        """文字列表現を返す。"""
        if self == AnnouncementType.REGULAR:
            return "通常開催"
        elif self == AnnouncementType.LIGHTNING_TALK:
            return "LT開催"
        elif self == AnnouncementType.REST:
            return "おやすみ"
        return self.name
