"""Работа с SQLite через SQLAlchemy ORM."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from rps.logic import RoundResult
from rps.models import Base, Round

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Ожидаемая ошибка работы с базой данных."""


def _describe(exc: SQLAlchemyError) -> str:
    return str(getattr(exc, "orig", None) or exc)


@contextmanager
def _db_errors(session: Session, action: str) -> Iterator[None]:
    """Откатить транзакцию и превратить ошибку SQLAlchemy в DatabaseError."""
    try:
        yield
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Ошибка БД (%s): %s", action, _describe(exc))
        raise DatabaseError(f"не удалось {action}: {_describe(exc)}") from exc


@contextmanager
def open_session(db_path: str | Path = "stats.db") -> Iterator[Session]:
    """Открыть сессию, создав таблицы при первом запуске.

    Сессия и соединения с базой гарантированно освобождаются при выходе.
    ":memory:" даёт базу в оперативной памяти.
    """
    engine = create_engine(f"sqlite:///{db_path}")
    try:
        try:
            Base.metadata.create_all(engine)
        except SQLAlchemyError as exc:
            logger.error("Не удалось открыть базу %s: %s", db_path, _describe(exc))
            raise DatabaseError(
                f"не удалось открыть базу {db_path}: {_describe(exc)}"
            ) from exc
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


def save_round(session: Session, round_result: RoundResult) -> None:
    """Сохранить раунд (отдельная транзакция на каждый раунд)."""
    with _db_errors(session, "сохранить раунд"):
        session.add(
            Round(
                player=round_result.player,
                computer=round_result.computer,
                result=round_result.result,
            )
        )
        session.commit()
    logger.info(
        "Раунд сохранён: игрок=%s компьютер=%s результат=%s",
        round_result.player,
        round_result.computer,
        round_result.result,
    )


def _count_by(session: Session, column) -> dict[str, int]:
    rows = session.execute(select(column, func.count()).group_by(column)).all()
    return {key: count for key, count in rows}


def count_results(session: Session) -> dict[str, int]:
    """Сколько раундов закончилось каждым результатом."""
    with _db_errors(session, "прочитать результаты"):
        return _count_by(session, Round.result)


def count_player_signs(session: Session) -> dict[str, int]:
    """Сколько раз игрок использовал каждый знак."""
    with _db_errors(session, "прочитать знаки игрока"):
        return _count_by(session, Round.player)


def count_computer_signs(session: Session) -> dict[str, int]:
    """Сколько раз компьютер использовал каждый знак."""
    with _db_errors(session, "прочитать знаки компьютера"):
        return _count_by(session, Round.computer)
