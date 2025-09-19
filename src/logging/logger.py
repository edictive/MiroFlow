# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

import atexit
import logging
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Literal

import hydra
from logging.handlers import RotatingFileHandler
from rich.console import Console
from rich.logging import RichHandler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE_ENV = "LOGGER_FILE"
LOG_DIR_ENV = "LOGGER_DIR"


def _determine_log_file() -> Path:
    """Resolve the log file path and ensure the directory exists."""
    env_file = os.getenv(LOG_FILE_ENV)
    if env_file:
        log_path = Path(env_file)
        if not log_path.is_absolute():
            log_path = PROJECT_ROOT / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path

    log_dir = Path(os.getenv(LOG_DIR_ENV, DEFAULT_LOG_DIR))
    if not log_dir.is_absolute():
        log_dir = PROJECT_ROOT / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir / f"miroflow_{timestamp}.log"


@lru_cache
def bootstrap_logger(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | int = "INFO",
    logger: logging.Logger | None = None,
) -> logging.Logger:
    """Configure only this logger, not the root logger"""
    if logger is None:
        logger = logging.getLogger("miroflow")
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

    # use rich for better readability of stack trace.
    handler = RichHandler(
        console=Console(
            stderr=True,
            width=200,
            color_system=None,  # Disable colors to avoid ANSI escape sequences in log files
            force_terminal=False,  # Don't force terminal mode
            legacy_windows=False,
        ),
        rich_tracebacks=True,
        tracebacks_suppress=[hydra],
        tracebacks_show_locals=True,
        show_level=False,
    )
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    log_file_handler = RotatingFileHandler(
        _determine_log_file(),
        maxBytes=10 * 1024 * 1024,  # 10 MB per file
        backupCount=5,
        encoding="utf-8",
    )
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log_file_handler.setFormatter(file_formatter)
    logger.addHandler(log_file_handler)
    logger.setLevel(level)
    logger.propagate = False

    atexit.register(log_file_handler.close)

    return logger
