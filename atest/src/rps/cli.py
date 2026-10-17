import logging
from pathlib import Path

import click

from rps.db import (
    DatabaseError,
    count_computer_signs,
    count_player_signs,
    count_results,
    open_session,
    save_round,
)
from rps.logging_config import setup_logging
from rps.logic import (
    COMPUTER,
    DRAW,
    EMOJI,
    PLAYER,
    SIGNS,
    Score,
    build_stats_report,
    play_round,
)

logger = logging.getLogger(__name__)

ROUND_TEXT = {
    PLAYER: "вы выиграли! 🎉",
    COMPUTER: "выиграл компьютер 🤖",
    DRAW: "ничья 🤝",
}
GAME_TEXT = {
    PLAYER: "Вы победили в партии!",
    COMPUTER: "Компьютер победил в партии.",
    DRAW: "В партии ничья.",
}


@click.group()
@click.option(
    "--db",
    type=click.Path(dir_okay=False, path_type=Path),
    default="stats.db",
    envvar="RPS_DB",
    show_default=True,
    help="Файл базы данных SQLite.",
)
@click.option(
    "--log-file",
    type=click.Path(dir_okay=False, path_type=Path),
    default="app.log",
    envvar="RPS_LOG_FILE",
    show_default=True,
    help="Файл журнала.",
)
@click.pass_context
def cli(ctx: click.Context, db: Path, log_file: Path) -> None:
    """Камень, ножницы, бумага против компьютера."""
    try:
        setup_logging(log_file)
    except OSError as exc:
        raise click.ClickException(f"не удалось открыть лог {log_file}: {exc}") from exc
    ctx.obj = {"db": db}


@cli.command()
@click.option(
    "--rounds",
    "-r",
    type=click.IntRange(min=1),
    default=3,
    show_default=True,
    help="Сколько раундов сыграть.",
)
@click.pass_obj
def play(obj: dict, rounds: int) -> None:
    """Сыграть партию."""
    logger.info("Начало партии: раундов=%d", rounds)
    score = Score()
    try:
        with open_session(obj["db"]) as session:
            for number in range(1, rounds + 1):
                choice = click.prompt(
                    f"Раунд {number}/{rounds}. Ваш выбор",
                    type=click.Choice(SIGNS, case_sensitive=False),
                )
                result = play_round(choice)
                save_round(session, result)
                score.add(result.result)
                click.echo(
                    f"Вы: {EMOJI[result.player]} {result.player}   "
                    f"Компьютер: {EMOJI[result.computer]} {result.computer}"
                )
                click.echo(f"Результат: {ROUND_TEXT[result.result]}\n")
    except DatabaseError as exc:
        raise click.ClickException(f"ошибка базы данных: {exc}") from exc
    except click.Abort:
        logger.warning("Партия прервана пользователем")
        raise

    logger.info(
        "Партия завершена: игрок=%d компьютер=%d ничьи=%d",
        score.player,
        score.computer,
        score.draw,
    )
    click.echo(
        f"Итоговый счёт — Игрок: {score.player}, "
        f"Компьютер: {score.computer}, Ничьи: {score.draw}"
    )
    click.echo(GAME_TEXT[score.winner])


@cli.command()
@click.option(
    "--view",
    type=click.Choice(["abs", "rel"]),
    default=None,
    help="abs — числа, rel — проценты; без опции — оба вида.",
)
@click.pass_obj
def stats(obj: dict, view: str | None) -> None:
    """Показать статистику всех сыгранных раундов."""
    try:
        with open_session(obj["db"]) as session:
            results = count_results(session)
            player_signs = count_player_signs(session)
            computer_signs = count_computer_signs(session)
    except DatabaseError as exc:
        raise click.ClickException(f"ошибка базы данных: {exc}") from exc

    if not results:
        click.echo("Пока нет сыгранных раундов. Начните игру командой: rps play")
        return
    logger.info("Показана статистика (view=%s)", view)
    for line in build_stats_report(results, player_signs, computer_signs, view):
        click.echo(line)
