"""Настройка логирования в файл app.log."""

import logging
from pathlib import Path

LOGGER_NAME = "rps"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def shutdown_logging() -> None:
    """Закрыть и убрать все файловые обработчики логгера приложения."""
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def setup_logging(log_file: str | Path = "app.log") -> logging.Logger:
    """Направить логи приложения в файл. Безопасно вызывать повторно.

    Raises:
        OSError: если файл лога нельзя открыть для записи.
    """
    shutdown_logging()
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
