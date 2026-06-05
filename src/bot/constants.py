# src/bot/constants.py
"""Bot共通の定数を定義するモジュール。"""

from enum import Enum, auto
from typing import override


# リアクション絵文字
class ReactionEmoji:
    """初回告知メッセージに付与するリアクション絵文字。"""

    REGULAR = "👍"  # 通常開催
    LIGHTNING_TALK = "⚡"  # LT開催
    WORKSPACE = "🛠️"  # 作業部屋開催
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

    # 全曜日 (表示順・バリデーション用)
    ALL = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]

    # 曜日対応マップ（文字列→数値、月=0〜日=6）
    MAP_TO_INT = {day: i for i, day in enumerate(ALL)}

    # 曜日対応マップ（日本語）
    JP_WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]

    @classmethod
    def to_int(cls, weekday_str: str) -> int:
        """文字列の曜日を数値に変換する。

        Args:
            weekday_str: 変換する曜日の文字列

        Returns:
            曜日の数値表現（0-6、月-日）。未知の値は日曜日(6)
        """
        return cls.MAP_TO_INT.get(weekday_str, 6)

    @classmethod
    def to_jp(cls, weekday_int: int) -> str:
        """数値の曜日を日本語表記に変換する。

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
    CONFIG_PATH = "CONFIG_PATH"
    CONFIG_OVERRIDES_PATH = "CONFIG_OVERRIDES_PATH"
    STATE_PATH = "STATE_PATH"


# アナウンスメントタイプ
class AnnouncementType(Enum):
    """今週のML集会の開催種別を定義する列挙型。"""

    REGULAR = auto()  # 通常開催
    LIGHTNING_TALK = auto()  # LT開催
    WORKSPACE = auto()  # 作業部屋開催
    REST = auto()  # おやすみ

    @override
    def __str__(self) -> str:
        """日本語の表示名を返す。"""
        return _TYPE_LABELS[self]


_TYPE_LABELS = {
    AnnouncementType.REGULAR: "通常開催",
    AnnouncementType.LIGHTNING_TALK: "LT開催",
    AnnouncementType.WORKSPACE: "作業部屋開催",
    AnnouncementType.REST: "おやすみ",
}

# リアクション絵文字 → 開催種別の写像 (リアクションによる種別選択に使用)
REACTION_TO_TYPE = {
    ReactionEmoji.REGULAR: AnnouncementType.REGULAR,
    ReactionEmoji.LIGHTNING_TALK: AnnouncementType.LIGHTNING_TALK,
    ReactionEmoji.WORKSPACE: AnnouncementType.WORKSPACE,
    ReactionEmoji.REST: AnnouncementType.REST,
}

# `/plan set` や `/open` の引数に使う短い種別名 ↔ 開催種別の写像
TYPE_BY_SLUG = {
    "regular": AnnouncementType.REGULAR,
    "lt": AnnouncementType.LIGHTNING_TALK,
    "workspace": AnnouncementType.WORKSPACE,
    "rest": AnnouncementType.REST,
}
SLUG_BY_TYPE = {
    announcement_type: slug for slug, announcement_type in TYPE_BY_SLUG.items()
}


# 設定ファイルのセクションとキー
class ConfigKeys:
    """設定ファイルのセクションとキー。"""

    # セクション
    SECTION_SETTINGS = "settings"
    SECTION_CHANNELS = "channels"
    SECTION_PERMISSIONS = "permissions"
    SECTION_TEMPLATES = "templates"

    # 基本設定キー
    KEY_ANNOUNCE_TIME = "announce_time"  # 初回告知の時刻 (日曜)
    KEY_ANNOUNCE_WEEKDAY = "announce_weekday"  # 初回告知の曜日 (日曜)
    KEY_EVENT_TIME = "event_time"  # 開催時刻 (水曜21:30、文面表示用)
    KEY_EVENT_WEEKDAY = "event_weekday"  # 開催曜日 (水曜、日付計算用)
    KEY_ACTION_ROLE = "action_role"  # 初回告知でメンションするロール
    KEY_DEFAULT_URL = "default_url"

    # チャンネルキー
    KEY_ANNOUNCE_CHANNEL_ID = "announce_channel_id"

    # 権限キー
    KEY_ADMIN_ROLES = "admin_roles"
    KEY_MODERATOR_ROLES = "moderator_roles"
    KEY_LT_ADMIN_ROLES = "lt_admin_roles"

    # 初回告知テンプレートキー (種別ごと)
    ANNOUNCE_TEMPLATE_KEYS = {
        AnnouncementType.REGULAR: "announce_regular",
        AnnouncementType.LIGHTNING_TALK: "announce_lightning_talk",
        AnnouncementType.WORKSPACE: "announce_workspace",
        AnnouncementType.REST: "announce_rest",
    }

    # 開催 (/open) テンプレートキー (種別ごと、おやすみは無し)
    OPEN_TEMPLATE_KEYS = {
        AnnouncementType.REGULAR: "open_regular",
        AnnouncementType.LIGHTNING_TALK: "open_lightning_talk",
        AnnouncementType.WORKSPACE: "open_workspace",
    }
