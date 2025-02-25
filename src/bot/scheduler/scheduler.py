"""Scheduler for periodic job execution.

This module implements a scheduler for running jobs at specific times on
specific days of the week.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from datetime import datetime, timedelta
from typing import Any

from bot.config.settings import BotSettings

logger = logging.getLogger(__name__)


class JobScheduler:
    """Scheduler for running jobs at specific times.

    Handles the scheduling and execution of jobs at configured times on
    configured days of the week.
    """

    # Mapping of weekday names to numbers (0 is Monday, 6 is Sunday)
    WEEKDAY_MAP = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

    def __init__(self, settings: BotSettings):
        """Initialize the job scheduler.

        Args:
            settings: The bot settings containing schedule configuration.
        """
        self.settings = settings
        self.jobs: dict[str, list[dict[str, Any]]] = {"confirm": [], "announce": []}
        self.running = False
        self.tasks: list[asyncio.Task[None]] = []

    def add_confirmation_job(
        self, job: Callable[..., Coroutine[Any, Any, None]], *args: Any, **kwargs: Any
    ) -> None:
        """Add a job to run on the confirmation weekday.

        Args:
            job: The coroutine function to run.
            *args: Positional arguments to pass to the job.
            **kwargs: Keyword arguments to pass to the job.
        """
        self.jobs["confirm"].append({"func": job, "args": args, "kwargs": kwargs})

    def add_announcement_job(
        self, job: Callable[..., Coroutine[Any, Any, None]], *args: Any, **kwargs: Any
    ) -> None:
        """Add a job to run on the announcement weekday.

        Args:
            job: The coroutine function to run.
            *args: Positional arguments to pass to the job.
            **kwargs: Keyword arguments to pass to the job.
        """
        self.jobs["announce"].append({"func": job, "args": args, "kwargs": kwargs})

    def start(self) -> None:
        """Start the scheduler.

        Creates tasks for each job type and starts them running.
        """
        self.running = True
        self.tasks = [
            asyncio.create_task(self._run_jobs_on_schedule("confirm")),
            asyncio.create_task(self._run_jobs_on_schedule("announce")),
        ]
        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler.

        Cancels all running tasks and marks the scheduler as stopped.
        """
        self.running = False
        for task in self.tasks:
            task.cancel()
        logger.info("Scheduler stopped")

    async def _run_jobs_on_schedule(self, job_type: str) -> None:
        """Run jobs of the specified type on schedule.

        Continuously checks if it's time to run the jobs and executes them
        when the scheduled time arrives.

        Args:
            job_type: The type of jobs to run ("confirm" or "announce").
        """
        while self.running:
            try:
                # Determine which weekday and time to use
                if job_type == "confirm":
                    target_weekday = self.WEEKDAY_MAP.get(
                        self.settings.confirm_weekday, 3
                    )  # Default to Thu
                    target_time = self.settings.confirm_time
                else:  # "announce"
                    target_weekday = self.WEEKDAY_MAP.get(
                        self.settings.announce_weekday, 6
                    )  # Default to Sun
                    target_time = self.settings.announce_time

                # Calculate time until next scheduled run
                now = datetime.now()
                days_ahead = (target_weekday - now.weekday()) % 7

                # If it's today and the time has already passed, schedule for next week
                if days_ahead == 0 and now.time() >= target_time:
                    days_ahead = 7

                next_run = datetime.combine(
                    now.date() + timedelta(days=days_ahead), target_time
                )

                # Calculate seconds until next run
                seconds_until_next_run = (next_run - now).total_seconds()

                logger.info(
                    f"Next {job_type} jobs scheduled to run in "
                    f"{seconds_until_next_run:.2f} seconds "
                    f"({next_run.strftime('%Y-%m-%d %H:%M:%S')})"
                )

                # Wait until the scheduled time
                await asyncio.sleep(seconds_until_next_run)

                # Run all jobs of this type
                for job in self.jobs[job_type]:
                    try:
                        await job["func"](*job["args"], **job["kwargs"])
                    except Exception as e:
                        logger.error(f"Error running {job_type} job: {e}")

                # Sleep a bit to avoid running jobs multiple times if execution is fast
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info(f"{job_type} scheduler task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in {job_type} scheduler: {e}")
                # Sleep a bit before retrying
                await asyncio.sleep(10)
