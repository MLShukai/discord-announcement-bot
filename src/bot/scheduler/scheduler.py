# src/bot/scheduler/scheduler.py
"""定期的なタスク実行を担当するスケジューラモジュール。"""

import asyncio
import datetime
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from ..constants import Weekday


class TaskScheduler:
    """タスクスケジューラクラス。

    指定した時間と曜日に定期的にタスクを実行する。
    """

    def __init__(self):
        """タスクスケジューラを初期化する。"""
        self.logger = logging.getLogger("announce-bot.scheduler")
        self.tasks: dict[str, asyncio.Task[None]] = {}

    def schedule_daily_task(
        self,
        task_id: str,
        time_str: str,
        weekday: str | None,
        callback: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        """指定した時間と曜日に実行するタスクをスケジュールする。

        Args:
            task_id: タスクの一意識別子
            time_str: 実行時間 (HH:MM形式)
            weekday: 実行曜日 (3文字略称) または毎日実行の場合はNone
            callback: タスク実行時に呼び出すコルーチン
        """
        # 同じIDの既存タスクがある場合はキャンセル
        if task_id in self.tasks and not self.tasks[task_id].done():
            self.tasks[task_id].cancel()
            self.logger.info(f"既存のタスクをキャンセルしました: {task_id}")

        # 新しいタスクを作成して開始
        self.tasks[task_id] = asyncio.create_task(
            self._run_at_time(time_str, weekday, callback)
        )

        when = f"毎日 {time_str}" if weekday is None else f"{weekday}曜日 {time_str}"
        self.logger.info(f"タスク {task_id} をスケジュールしました: {when}")

    async def _run_at_time(
        self,
        time_str: str,
        weekday: str | None,
        callback: Callable[[], Coroutine[Any, Any, None]],
    ) -> None:
        """指定時間と曜日にタスクを実行する内部メソッド。

        Args:
            time_str: 実行時間 (HH:MM形式)
            weekday: 実行曜日 (3文字略称) または毎日実行の場合はNone
            callback: タスク実行時に呼び出すコルーチン
        """
        target_weekday = Weekday.to_int(weekday) if weekday else None

        while True:
            now = datetime.datetime.now()

            # 対象時間を解析
            hour, minute = map(int, time_str.split(":"))
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # 対象時間が当日の過去の場合は明日に設定
            if target_time <= now:
                target_time += datetime.timedelta(days=1)

            # 特定曜日指定がある場合は日付を調整
            if target_weekday is not None:
                days_ahead = target_weekday - target_time.weekday()
                if days_ahead < 0:  # 今週の指定曜日が過ぎた場合
                    days_ahead += 7
                elif (
                    days_ahead == 0 and target_time.time() < now.time()
                ):  # 当日だが時間が過ぎた場合
                    days_ahead = 7

                target_time = target_time.replace(
                    day=target_time.day + days_ahead, hour=hour, minute=minute
                )

            # 待機秒数を計算
            seconds_to_wait = (target_time - now).total_seconds()
            self.logger.debug(
                f"{seconds_to_wait:.1f}秒待機します（目標時刻: {target_time}）"
            )

            try:
                # 対象時間まで待機
                await asyncio.sleep(seconds_to_wait)

                # コールバックを実行
                self.logger.info(
                    f"スケジュールされたタスクを実行します: {datetime.datetime.now()}"
                )
                await callback()

            except asyncio.CancelledError:
                self.logger.info("タスクがキャンセルされました")
                break
            except Exception as e:
                self.logger.error(
                    f"スケジュールされたタスクでエラーが発生しました: {e}"
                )
                # 連続エラーを避けるため少し待機
                await asyncio.sleep(60)

    def cancel_all_tasks(self) -> None:
        """すべてのスケジュールされたタスクをキャンセルする。"""
        for task_id, task in self.tasks.items():
            if not task.done():
                task.cancel()
                self.logger.info(f"タスクをキャンセルしました: {task_id}")

        self.tasks.clear()
