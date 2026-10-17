"""Бизнес-логика игры: не зависит ни от Click, ни от базы данных."""

import random
from dataclasses import dataclass
from typing import Literal

SIGNS = ("rock", "paper", "scissors")
EMOJI = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

PLAYER = "player"
COMPUTER = "computer"
DRAW = "draw"
RESULTS = (PLAYER, COMPUTER, DRAW)

# Ключ побеждает значение.
BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}

View = Literal["abs", "rel"] | None


def determine_winner(player: str, computer: str) -> str:
    """Вернуть "player", "computer" или "draw".

    Raises:
        ValueError: если один из знаков не входит в SIGNS.
    """
    for sign in (player, computer):
        if sign not in SIGNS:
            raise ValueError(f"недопустимый знак: {sign!r}")
    if player == computer:
        return DRAW
    return PLAYER if BEATS[player] == computer else COMPUTER


def choose_computer_sign() -> str:
    """Случайный выбор компьютера."""
    return random.choice(SIGNS)


@dataclass(frozen=True)
class RoundResult:
    player: str
    computer: str
    result: str


def play_round(player: str, computer: str | None = None) -> RoundResult:
    """Сыграть раунд. Если знак компьютера не задан — выбрать случайно."""
    if computer is None:
        computer = choose_computer_sign()
    return RoundResult(player, computer, determine_winner(player, computer))


@dataclass
class Score:
    """Счёт одной партии."""

    player: int = 0
    computer: int = 0
    draw: int = 0

    def add(self, result: str) -> None:
        if result not in RESULTS:
            raise ValueError(f"недопустимый результат: {result!r}")
        setattr(self, result, getattr(self, result) + 1)

    @property
    def winner(self) -> str:
        if self.player == self.computer:
            return DRAW
        return PLAYER if self.player > self.computer else COMPUTER


def format_stat(count: int, total: int, view: View) -> str:
    """Отформатировать число: абсолютное, относительное или оба вида."""
    percent = count / total * 100 if total else 0
    if view == "abs":
        return f"{count}"
    if view == "rel":
        return f"{percent:.1f}%"
    return f"{count} ({percent:.1f}%)"


def build_stats_report(
    results: dict[str, int],
    player_signs: dict[str, int],
    computer_signs: dict[str, int],
    view: View,
) -> list[str]:
    """Собрать строки отчёта. Проценты считаются от числа раундов."""
    total = sum(results.get(r, 0) for r in RESULTS)

    def stat(counts: dict[str, int], key: str) -> str:
        return format_stat(counts.get(key, 0), total, view)

    def signs_line(counts: dict[str, int]) -> str:
        return ", ".join(f"{sign} {stat(counts, sign)}" for sign in SIGNS)

    return [
        f"Победы игрока: {stat(results, PLAYER)}",
        f"Победы компьютера: {stat(results, COMPUTER)}",
        f"Ничьи: {stat(results, DRAW)}",
        f"Игрок:     {signs_line(player_signs)}",
        f"Компьютер: {signs_line(computer_signs)}",
    ]
