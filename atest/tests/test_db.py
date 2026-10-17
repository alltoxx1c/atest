import pytest
from sqlalchemy import func, select

from rps.db import (
    DatabaseError,
    count_computer_signs,
    count_player_signs,
    count_results,
    open_session,
    save_round,
)
from rps.logic import RoundResult
from rps.models import Round


def test_counts_on_empty_database(session):
    assert count_results(session) == {}
    assert count_player_signs(session) == {}
    assert count_computer_signs(session) == {}


def test_save_round_persists_data(session):
    save_round(session, RoundResult("rock", "scissors", "player"))
    row = session.execute(select(Round)).scalar_one()
    assert (row.player, row.computer, row.result) == ("rock", "scissors", "player")
    assert row.created_at is not None


def test_counts_aggregate_all_rounds(session):
    rounds = [
        RoundResult("rock", "scissors", "player"),
        RoundResult("rock", "paper", "computer"),
        RoundResult("paper", "paper", "draw"),
        RoundResult("rock", "rock", "draw"),
    ]
    for item in rounds:
        save_round(session, item)

    assert count_results(session) == {"player": 1, "computer": 1, "draw": 2}
    assert count_player_signs(session) == {"rock": 3, "paper": 1}
    assert count_computer_signs(session) == {
        "scissors": 1,
        "paper": 2,
        "rock": 1,
    }


def test_save_round_failure_rolls_back_and_raises_database_error(session):
    # player = NULL нарушает NOT NULL и вызывает IntegrityError.
    bad = RoundResult(None, "rock", "draw")
    with pytest.raises(DatabaseError, match="сохранить раунд"):
        save_round(session, bad)

    # Сессия после отката остаётся рабочей.
    save_round(session, RoundResult("rock", "rock", "draw"))
    assert session.execute(select(func.count()).select_from(Round)).scalar_one() == 1


def test_open_session_creates_file_and_persists(tmp_path):
    db_file = tmp_path / "game.db"
    with open_session(db_file) as session:
        save_round(session, RoundResult("paper", "rock", "player"))
    assert db_file.exists()

    with open_session(db_file) as session:
        assert count_results(session) == {"player": 1}


def test_open_session_unreachable_path_raises_database_error(tmp_path):
    missing = tmp_path / "no_such_dir" / "game.db"
    with (
        pytest.raises(DatabaseError, match="не удалось открыть базу"),
        open_session(missing),
    ):
        pass
