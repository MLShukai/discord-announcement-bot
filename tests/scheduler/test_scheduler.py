# tests/scheduler/test_scheduler.py
"""Tests for the task scheduler module."""

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.scheduler.scheduler import TaskScheduler, compute_next_run


# 2026-06-01 は月曜、06-03 は水曜、06-07 は日曜
def test_compute_next_run_future_same_day():
    """When the target time is later today on the target weekday, run today."""
    now = datetime.datetime(2026, 6, 3, 9, 0)  # 水曜 09:00
    result = compute_next_run(now, 2, 12, 0)  # 水曜 12:00
    assert result == datetime.datetime(2026, 6, 3, 12, 0)


def test_compute_next_run_past_same_day_wraps_week():
    """When the target time already passed today, run next week."""
    now = datetime.datetime(2026, 6, 3, 15, 0)  # 水曜 15:00
    result = compute_next_run(now, 2, 12, 0)  # 水曜 12:00 は過ぎている
    assert result == datetime.datetime(2026, 6, 10, 12, 0)


def test_compute_next_run_other_weekday():
    """Target on a later weekday this week."""
    now = datetime.datetime(2026, 6, 1, 9, 0)  # 月曜
    result = compute_next_run(now, 6, 12, 0)  # 次の日曜
    assert result == datetime.datetime(2026, 6, 7, 12, 0)


def test_compute_next_run_weekday_already_passed():
    """Target weekday earlier in the week wraps to next week."""
    now = datetime.datetime(2026, 6, 5, 9, 0)  # 金曜
    result = compute_next_run(now, 2, 12, 0)  # 水曜は今週分が過ぎた
    assert result == datetime.datetime(2026, 6, 10, 12, 0)


@pytest.fixture
def scheduler():
    """Create a TaskScheduler instance for testing."""
    return TaskScheduler()


def test_scheduler_init(scheduler):
    """Test TaskScheduler initialization."""
    assert scheduler.tasks == {}


def test_schedule_weekly_task(scheduler):
    """Scheduling registers a task under its id."""
    callback_mock = AsyncMock()
    with patch("asyncio.create_task") as create_task_mock:
        scheduler.schedule_weekly_task("test_task", "Sun", "12:00", callback_mock)
        assert create_task_mock.called
        assert "test_task" in scheduler.tasks
        create_task_mock.call_args.args[0].close()  # 未await警告を避ける


def test_schedule_replaces_existing_task(scheduler):
    """Scheduling an existing id cancels the previous task."""
    callback_mock = AsyncMock()
    task_mock = MagicMock()
    task_mock.done.return_value = False
    scheduler.tasks["test_task"] = task_mock

    with patch("asyncio.create_task") as create_task_mock:
        scheduler.schedule_weekly_task("test_task", "Sun", "12:00", callback_mock)
        assert task_mock.cancel.called
        assert create_task_mock.called
        create_task_mock.call_args.args[0].close()  # 未await警告を避ける


def test_cancel_all_tasks(scheduler):
    """Only not-done tasks are canceled and the dict is cleared."""
    task1 = MagicMock()
    task1.done.return_value = False
    task2 = MagicMock()
    task2.done.return_value = True
    scheduler.tasks = {"task1": task1, "task2": task2}

    scheduler.cancel_all_tasks()

    assert task1.cancel.called
    assert not task2.cancel.called
    assert scheduler.tasks == {}
