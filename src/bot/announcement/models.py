# src/bot/announcement/models.py
"""告知に関連するデータモデルを定義するモジュール。"""

from dataclasses import dataclass
from typing import override


@dataclass
class LTInfo:
    """LT（ライトニングトーク）の情報を格納するデータクラス。"""

    speaker_name: str | None = None
    title: str | None = None
    url: str | None = None

    @property
    def is_complete(self) -> bool:
        """全てのLT情報が設定されているかを確認する。

        Returns:
            全ての項目が設定されていればTrue、そうでなければFalse
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
