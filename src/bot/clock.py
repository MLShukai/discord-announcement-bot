# src/bot/clock.py
"""時刻ソースを抽象化するモジュール。

スケジューラや告知サービスが現在時刻を取得する経路を差し替え可能にし、 テストで時刻を決定化できるようにする。
"""

import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """現在時刻・日付を提供する時刻ソース。"""

    def now(self) -> datetime.datetime:
        """現在のローカル日時を返す。"""
        ...

    def today(self) -> datetime.date:
        """現在のローカル日付を返す。"""
        ...


class SystemClock:
    """システム時計に基づく既定の `Clock` 実装。"""

    def now(self) -> datetime.datetime:
        """システムの現在日時を返す。

        Returns:
            ローカルタイムゾーンの現在日時
        """
        return datetime.datetime.now()

    def today(self) -> datetime.date:
        """システムの現在日付を返す。

        Returns:
            ローカルタイムゾーンの現在日付
        """
        return datetime.datetime.now().date()
