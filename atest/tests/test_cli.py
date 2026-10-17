import pytest
from click.testing import CliRunner

from rps.cli import cli
from rps.db import count_results, open_session


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def paths(tmp_path):
    return {"db": tmp_path / "stats.db", "log": tmp_path / "app.log"}


def invoke(runner, paths, args, **kwargs):
    base = ["--db", str(paths["db"]), "--log-file", str(paths["log"])]
    return runner.invoke(cli, base + args, **kwargs)


@pytest.fixture
def computer_plays_scissors(monkeypatch):
    monkeypatch.setattr("rps.logic.random.choice", lambda seq: "scissors")


def test_play_default_three_rounds(runner, paths, computer_plays_scissors):
    result = invoke(runner, paths, ["play"], input="rock\npaper\nscissors\n")
    assert result.exit_code == 0
    assert "Раунд 3/3" in result.output
    assert "🪨" in result.output
    assert "✂️" in result.output
    assert "Итоговый счёт — Игрок: 1, Компьютер: 1, Ничьи: 1" in result.output


def test_play_custom_rounds_and_saves_each_round(
    runner, paths, computer_plays_scissors
):
    result = invoke(runner, paths, ["play", "-r", "2"], input="rock\nrock\n")
    assert result.exit_code == 0
    assert "Вы победили в партии!" in result.output
    with open_session(paths["db"]) as session:
        assert count_results(session) == {"player": 2}


def test_play_reprompts_on_invalid_choice(runner, paths, computer_plays_scissors):
    result = invoke(runner, paths, ["play", "-r", "1"], input="lizard\nrock\n")
    assert result.exit_code == 0
    assert "lizard" in result.output
    assert "Итоговый счёт" in result.output


@pytest.mark.parametrize("value", ["0", "-1", "abc"])
def test_play_invalid_rounds_exit_code(runner, paths, value):
    result = invoke(runner, paths, ["play", "--rounds", value])
    assert result.exit_code == 2
    assert "Error" in result.output


def test_play_abort_returns_nonzero_and_keeps_saved_rounds(
    runner, paths, computer_plays_scissors
):
    # Один раунд сыгран, затем ввод заканчивается (аналог Ctrl+D).
    result = invoke(runner, paths, ["play", "-r", "3"], input="rock\n")
    assert result.exit_code != 0
    with open_session(paths["db"]) as session:
        assert count_results(session) == {"player": 1}


def test_stats_empty_database(runner, paths):
    result = invoke(runner, paths, ["stats"])
    assert result.exit_code == 0
    assert "Пока нет сыгранных раундов" in result.output


def test_stats_views(runner, paths, computer_plays_scissors):
    invoke(runner, paths, ["play", "-r", "2"], input="rock\npaper\n")

    both = invoke(runner, paths, ["stats"])
    assert both.exit_code == 0
    assert "Победы игрока: 1 (50.0%)" in both.output
    assert "Победы компьютера: 1 (50.0%)" in both.output
    assert "Игрок:     rock 1 (50.0%), paper 1 (50.0%), scissors 0 (0.0%)" in (
        both.output
    )

    absolute = invoke(runner, paths, ["stats", "--view", "abs"])
    assert "Победы игрока: 1\n" in absolute.output
    assert "%" not in absolute.output

    relative = invoke(runner, paths, ["stats", "--view", "rel"])
    assert "Ничьи: 0.0%" in relative.output


def test_stats_invalid_view(runner, paths):
    result = invoke(runner, paths, ["stats", "--view", "total"])
    assert result.exit_code == 2


def test_database_error_gives_message_and_nonzero_exit(runner, tmp_path):
    paths = {"db": tmp_path / "missing_dir" / "stats.db", "log": tmp_path / "app.log"}
    result = invoke(runner, paths, ["stats"])
    assert result.exit_code == 1
    assert "ошибка базы данных" in result.output
    assert "Traceback" not in result.output


def test_unwritable_log_file_gives_clean_error(runner, tmp_path):
    paths = {"db": tmp_path / "s.db", "log": tmp_path / "no_dir" / "app.log"}
    result = invoke(runner, paths, ["stats"])
    assert result.exit_code == 1
    assert "не удалось открыть лог" in result.output


def test_events_and_errors_are_logged(runner, paths, computer_plays_scissors):
    invoke(runner, paths, ["play", "-r", "1"], input="rock\n")
    bad = {"db": paths["db"].parent / "nope" / "x.db", "log": paths["log"]}
    invoke(runner, bad, ["stats"])

    log = paths["log"].read_text(encoding="utf-8")
    assert "Начало партии" in log
    assert "Раунд сохранён" in log
    assert "Партия завершена" in log
    assert "ERROR" in log
