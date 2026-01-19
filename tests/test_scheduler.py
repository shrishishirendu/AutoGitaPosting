from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from gita_autoposter.agents.scheduler import SchedulerAgent


def test_scheduler_next_time_same_day() -> None:
    timezone = "Australia/Sydney"
    agent = SchedulerAgent(timezone, "07:00")
    now = datetime(2024, 1, 1, 6, 0, tzinfo=ZoneInfo(timezone))
    result = agent.next_scheduled_time(now)
    assert result.scheduled_time.hour == 7
    assert result.scheduled_time.day == 1


def test_scheduler_next_time_next_day() -> None:
    timezone = "Australia/Sydney"
    agent = SchedulerAgent(timezone, "07:00")
    now = datetime(2024, 1, 1, 8, 0, tzinfo=ZoneInfo(timezone))
    result = agent.next_scheduled_time(now)
    assert result.scheduled_time.hour == 7
    assert result.scheduled_time.day == 2
