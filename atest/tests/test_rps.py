import pytest

from rps.logic import (
    COMPUTER,
    DRAW,
    PLAYER,
    SIGNS,
    RoundResult,
    Score,
    build_stats_report,
    choose_computer_sign,
    determine_winner,
    format_stat,
    play_round,
)

ALL_COMBINATIONS = [
    ("rock", "rock", DRAW),
    ("rock", "paper", COMPUTER),
    ("rock", "scissors", PLAYER),
    ("paper", "rock", PLAYER),
    ("paper", "paper", DRAW),
    ("paper", "scissors", COMPUTER),
    ("scissors", "rock", COMPUTER),
    ("scissors", "paper", PLAYER),
    ("scissors", "scissors", DRAW),
]


@pytest.mark.parametrize(("player", "computer", "expected"), ALL_COMBINATIONS)
def test_determine_winner_all_nine_combinations(player, computer, expected):
    assert determine_winner(player, computer) == expected


def test_all_combinations_are_covered():
    assert len(ALL_COMBINATIONS) == len(SIGNS) ** 2


@pytest.mark.parametrize(
    ("player", "computer"),
    [("lizard", "rock"), ("rock", "spock"), ("", "rock"), ("ROCK", "rock")],
)
def test_determine_winner_rejects_unknown_sign(player, computer):
    with pytest.raises(ValueError, match="недопустимый знак"):
        determine_winner(player, computer)


def test_choose_computer_sign_returns_valid_sign():
    assert all(choose_computer_sign() in SIGNS for _ in range(50))


def test_play_round_with_fixed_computer_sign():
    assert play_round("rock", "scissors") == RoundResult("rock", "scissors", PLAYER)


def test_play_round_random_computer_is_consistent():
    result = play_round("paper")
    assert result.computer in SIGNS
    assert result.result == determine_winner("paper", result.computer)


def test_play_round_invalid_sign_raises():
    with pytest.raises(ValueError):
        play_round("fire", "rock")


def test_score_counts_results_and_winner():
    score = Score()
    for result in (PLAYER, PLAYER, COMPUTER, DRAW):
        score.add(result)
    assert (score.player, score.computer, score.draw) == (2, 1, 1)
    assert score.winner == PLAYER


def test_score_winner_computer_and_draw():
    score = Score()
    assert score.winner == DRAW
    score.add(COMPUTER)
    assert score.winner == COMPUTER


def test_score_rejects_unknown_result():
    with pytest.raises(ValueError):
        Score().add("nobody")


@pytest.mark.parametrize(
    ("count", "total", "view", "expected"),
    [
        (9, 20, "abs", "9"),
        (9, 20, "rel", "45.0%"),
        (9, 20, None, "9 (45.0%)"),
        (0, 0, None, "0 (0.0%)"),
        (0, 0, "rel", "0.0%"),
        (1, 3, "rel", "33.3%"),
    ],
)
def test_format_stat(count, total, view, expected):
    assert format_stat(count, total, view) == expected


def test_build_stats_report_both_views():
    report = build_stats_report(
        {PLAYER: 9, COMPUTER: 8, DRAW: 3},
        {"rock": 7, "paper": 8, "scissors": 5},
        {"rock": 6, "paper": 6, "scissors": 8},
        None,
    )
    assert report == [
        "Победы игрока: 9 (45.0%)",
        "Победы компьютера: 8 (40.0%)",
        "Ничьи: 3 (15.0%)",
        "Игрок:     rock 7 (35.0%), paper 8 (40.0%), scissors 5 (25.0%)",
        "Компьютер: rock 6 (30.0%), paper 6 (30.0%), scissors 8 (40.0%)",
    ]


def test_build_stats_report_abs_and_rel_with_missing_keys():
    absolute = build_stats_report({PLAYER: 1}, {"rock": 1}, {"paper": 1}, "abs")
    assert absolute[0] == "Победы игрока: 1"
    assert absolute[1] == "Победы компьютера: 0"
    assert absolute[3] == "Игрок:     rock 1, paper 0, scissors 0"

    relative = build_stats_report({PLAYER: 1}, {"rock": 1}, {"paper": 1}, "rel")
    assert relative[0] == "Победы игрока: 100.0%"
    assert relative[4] == "Компьютер: rock 0.0%, paper 100.0%, scissors 0.0%"
