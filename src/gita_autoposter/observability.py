from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any


_STANDARD_FIELDS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


class KeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcfromtimestamp(record.created).isoformat() + "Z"
        parts = [
            f"ts={timestamp}",
            f"level={record.levelname}",
            f"run_id={getattr(record, 'run_id', '-')}",
            f"stage={getattr(record, 'stage', '-')}",
            f"msg={self._quote(record.getMessage())}",
        ]
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_FIELDS and key not in {"run_id", "stage"}
        }
        for key, value in sorted(extras.items()):
            parts.append(f"{key}={self._quote(value)}")
        return " ".join(parts)

    @staticmethod
    def _quote(value: Any) -> str:
        text = str(value)
        if " " in text or "=" in text:
            text = text.replace('"', '\\"')
            return f"\"{text}\""
        return text


class RunLogger(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        extra = kwargs.setdefault("extra", {})
        extra.setdefault("run_id", self.extra.get("run_id"))
        return msg, kwargs


def setup_run_logger(run_id: str, run_dir: Path) -> RunLogger:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = logging.getLevelName(level_name)
    if isinstance(level, str):
        level = logging.INFO

    logger = logging.getLogger(f"gita_autoposter.run.{run_id}")
    logger.setLevel(level)
    logger.propagate = False
    logger.handlers.clear()

    formatter = KeyValueFormatter()

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    log_path = run_dir / "run.log"
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return RunLogger(logger, {"run_id": run_id})
