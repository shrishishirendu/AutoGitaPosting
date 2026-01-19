from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass
class ScheduleResult:
    scheduled_time: datetime


class SchedulerAgent:
    def __init__(self, timezone: str, post_time: str) -> None:
        self.timezone = ZoneInfo(timezone)
        self.post_time = post_time

    def next_scheduled_time(self, now: datetime | None = None) -> ScheduleResult:
        now = now or datetime.now(self.timezone)
        target_time = _parse_post_time(self.post_time)
        scheduled = datetime.combine(now.date(), target_time, tzinfo=self.timezone)
        if now >= scheduled:
            scheduled = scheduled + timedelta(days=1)
        return ScheduleResult(scheduled_time=scheduled)


def _parse_post_time(value: str) -> time:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("POST_TIME must be in HH:MM format.")
    hour = int(parts[0])
    minute = int(parts[1])
    return time(hour=hour, minute=minute)
