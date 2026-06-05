# src/bot/state/store.py
"""今週の開催種別やLT情報などの実行時状態を永続化するモジュール。

状態は JSON ファイルに保存し、Docker コンテナの再起動・再ビルドをまたいで 保持できるようにする。
"""

import datetime
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, override

from ..constants import AnnouncementType


@dataclass
class LTInfo:
    """LT（ライトニングトーク）の情報を格納するデータクラス。"""

    speaker_name: str | None = None
    title: str | None = None
    url: str | None = None

    @property
    def is_complete(self) -> bool:
        """発表者・タイトル・URL がすべて設定されているかを返す。

        Returns:
            すべて設定済みなら True
        """
        return (
            self.speaker_name is not None
            and self.title is not None
            and self.url is not None
        )

    def clear(self) -> None:
        """全てのLT情報をクリアする。"""
        self.speaker_name = None
        self.title = None
        self.url = None

    @override
    def __str__(self) -> str:
        """LT情報の文字列表現を返す。"""
        if not any([self.speaker_name, self.title, self.url]):
            return "LT情報は設定されていません"

        parts: list[str] = []
        if self.speaker_name is not None:
            parts.append(f"発表者: {self.speaker_name}")
        if self.title is not None:
            parts.append(f"タイトル: {self.title}")
        if self.url is not None:
            parts.append(f"URL: {self.url}")
        return "\n".join(parts)


@dataclass
class SessionState:
    """今週のML集会に関する永続化対象の状態。"""

    session_type: AnnouncementType = AnnouncementType.REGULAR
    lt: LTInfo = field(default_factory=LTInfo)
    announce_message_id: int | None = None
    target_event_date: datetime.date | None = None

    def to_dict(self) -> dict[str, Any]:
        """JSON 直列化可能な辞書へ変換する。

        Returns:
            状態を表す辞書
        """
        return {
            "session_type": self.session_type.name,
            "lt": {
                "speaker_name": self.lt.speaker_name,
                "title": self.lt.title,
                "url": self.lt.url,
            },
            "announce_message_id": self.announce_message_id,
            "target_event_date": (
                self.target_event_date.isoformat()
                if self.target_event_date is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionState":
        """辞書から状態を復元する。

        未知・欠損のフィールドは既定値にフォールバックする。

        Args:
            data: `to_dict` 形式の辞書

        Returns:
            復元された状態
        """
        session_type = AnnouncementType.__members__.get(
            data.get("session_type", ""), AnnouncementType.REGULAR
        )
        lt_raw = data.get("lt")
        lt_data: dict[str, Any] = lt_raw if isinstance(lt_raw, dict) else {}
        lt = LTInfo(
            speaker_name=lt_data.get("speaker_name"),
            title=lt_data.get("title"),
            url=lt_data.get("url"),
        )
        raw_date = data.get("target_event_date")
        target_event_date = datetime.date.fromisoformat(raw_date) if raw_date else None
        return cls(
            session_type=session_type,
            lt=lt,
            announce_message_id=data.get("announce_message_id"),
            target_event_date=target_event_date,
        )


class StateStore:
    """`SessionState` を JSON ファイルへ読み書きする永続化ストア。"""

    def __init__(self, path: str):
        """状態ストアを初期化し、既存ファイルがあれば読み込む。

        Args:
            path: 状態ファイルのパス
        """
        self.logger = logging.getLogger("announce-bot.state")
        self._path = path
        self._state = self._load()

    @property
    def state(self) -> SessionState:
        """現在の状態を返す。

        Returns:
            読み込み済みの状態オブジェクト
        """
        return self._state

    def _load(self) -> SessionState:
        """状態ファイルを読み込む。存在しない・壊れている場合は既定値を返す。"""
        if not os.path.exists(self._path):
            self.logger.info(f"状態ファイルが無いため既定値で開始します: {self._path}")
            return SessionState()
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            self.logger.info(f"状態を読み込みました: {self._path}")
            return SessionState.from_dict(data)
        except (OSError, ValueError) as e:
            self.logger.error(f"状態の読み込みに失敗しました (既定値で続行): {e}")
            return SessionState()

    def save(self) -> None:
        """現在の状態をファイルへ保存する。"""
        try:
            parent_dir = os.path.dirname(self._path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._state.to_dict(), f, ensure_ascii=False, indent=2)
            self.logger.debug(f"状態を保存しました: {self._path}")
        except OSError as e:
            self.logger.error(f"状態の保存に失敗しました: {e}")
            raise
