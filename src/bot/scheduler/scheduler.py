# src/bot/scheduler/scheduler.py
"""定期的なタスク実行を担当するスケジューラモジュール。"""

import asyncio
import datetime
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from ..clock import Clock, SystemClock
from ..constants import Weekday


def compute_next_run(
    now: datetime.datetime, weekday: int, hour: int, minute: int
) -> datetime.datetime:
    """指定曜日・時刻の次回実行日時を計算する純粋関数。

    Args:
        now: 基準となる現在日時
        weekday: 実行曜日（0-6、月-日）
        hour: 実行時（0-23）
        minute: 実行分（0-59）

    Returns:
        `now` より後で最も近い、指定曜日・時刻の日時

    >>> wed_noon = compute_next_run(
    ...     datetime.datetime(2026, 6, 1, 9, 0), 2, 12, 0
    ... )
    >>> wed_noon.isoformat()
    '2026-06-03T12:00:00'
    """
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    days_ahead = (weekday - candidate.weekday()) % 7
    if days_ahead == 0 and candidate <= now:
        days_ahead = 7
    return candidate + datetime.timedelta(days=days_ahead)


class TaskScheduler:
    """タスクスケジューラクラス。

    指定した曜日・時刻に毎週繰り返しタスクを実行する。
    """

    def __init__(self, clock: Clock | None = None):
        """タスクスケジューラを初期化する。

        Args:
            clock: 時刻ソース（未指定なら `SystemClock`）
        """
        self.logger = logging.getLogger("announce-bot.scheduler")
        self.clock = clock or SystemClock()
        self.tasks: dict[str, asyncio.Task[None]] = {}

    def schedule_weekly_task(
        self,
        task_id: str,
        weekday: str,
        time_str: str,
        callback: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        """指定曜日・時刻に毎週実行するタスクをスケジュールする。

        同じIDの既存タスクがあれば差し替える。

        Args:
            task_id: タスクの一意識別子
            weekday: 実行曜日（3文字略称）
            time_str: 実行時刻（HH:MM形式）
            callback: 実行時に呼び出すコルーチン
        """
        existing = self.tasks.get(task_id)
        if existing is not None and not existing.done():
            existing.cancel()
            self.logger.info(f"既存のタスクをキャンセルしました: {task_id}")

        self.tasks[task_id] = asyncio.create_task(
            self._run_weekly(weekday, time_str, callback)
        )
        self.logger.info(
            f"タスク {task_id} をスケジュールしました: {weekday}曜日 {time_str}"
        )

    async def _run_weekly(
        self,
        weekday: str,
        time_str: str,
        callback: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        """次回実行時刻まで待機してコールバックを呼ぶループ。

        Args:
            weekday: 実行曜日（3文字略称）
            time_str: 実行時刻（HH:MM形式）
            callback: 実行時に呼び出すコルーチン
        """
        target_weekday = Weekday.to_int(weekday)
        hour, minute = map(int, time_str.split(":"))

        while True:
            now = self.clock.now()
            target = compute_next_run(now, target_weekday, hour, minute)
            seconds_to_wait = (target - now).total_seconds()
            self.logger.debug(f"{seconds_to_wait:.1f}秒待機します（目標: {target}）")

            try:
                await asyncio.sleep(seconds_to_wait)
                self.logger.info(f"スケジュールタスクを実行します: {self.clock.now()}")
                await callback()
            except asyncio.CancelledError:
                self.logger.info("タスクがキャンセルされました")
                break
            except Exception as e:
                self.logger.error(f"スケジュールタスクでエラーが発生しました: {e}")
                # 連続エラーを避けるため少し待機
                await asyncio.sleep(60)

    def cancel_all_tasks(self) -> None:
        """すべてのスケジュールされたタスクをキャンセルする。"""
        for task_id, task in self.tasks.items():
            if not task.done():
                task.cancel()
                self.logger.info(f"タスクをキャンセルしました: {task_id}")
        self.tasks.clear()
