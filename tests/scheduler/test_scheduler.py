# tests/scheduler/test_scheduler.py
"""Tests for the task scheduler module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.scheduler.scheduler import TaskScheduler


@pytest.fixture
def scheduler():
    """Create a TaskScheduler instance for testing."""
    return TaskScheduler()


def test_scheduler_init(scheduler):
    """Test TaskScheduler initialization."""
    assert scheduler.tasks == {}


def test_schedule_daily_task(scheduler):
    """Test scheduling a daily task."""
    callback_mock = AsyncMock()

    with patch("asyncio.create_task") as create_task_mock:
        scheduler.schedule_daily_task("test_task", "12:00", "Mon", callback_mock)

        # Verify create_task was called
        assert create_task_mock.called

        # Verify task was added to tasks dict
        assert "test_task" in scheduler.tasks


def test_schedule_replaces_existing_task(scheduler):
    """Test scheduling a task with existing ID replaces old task."""
    callback_mock = AsyncMock()

    # Create a mock task that's not done
    task_mock = MagicMock()
    task_mock.done.return_value = False

    # Add it to the tasks dictionary
    scheduler.tasks["test_task"] = task_mock

    # Schedule a new task with the same ID
    with patch("asyncio.create_task") as create_task_mock:
        scheduler.schedule_daily_task("test_task", "12:00", "Mon", callback_mock)

        # Verify old task was canceled
        assert task_mock.cancel.called

        # Verify new task was created
        assert create_task_mock.called


def test_cancel_all_tasks(scheduler):
    """Test canceling all scheduled tasks."""
    # Create mock tasks
    task1 = MagicMock()
    task1.done.return_value = False

    task2 = MagicMock()
    task2.done.return_value = True  # Already done

    # Add tasks to scheduler
    scheduler.tasks = {"task1": task1, "task2": task2}

    # Cancel all tasks
    scheduler.cancel_all_tasks()

    # Verify only non-done tasks were canceled
    assert task1.cancel.called
    assert not task2.cancel.called

    # Verify tasks dict was cleared
    assert scheduler.tasks == {}
