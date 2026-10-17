Маркачёв Илья
# rps — «камень, ножницы, бумага» в терминале

CLI-утилита на Python ([Click](https://click.palletsprojects.com/)): игра против
компьютера со статистикой всех сыгранных раундов в SQLite
(через [SQLAlchemy](https://www.sqlalchemy.org/) ORM).

- `rps play` — сыграть партию; каждый раунд сразу сохраняется в базу.
- `rps stats` — статистика за всё время: победы игрока и компьютера, ничьи,
  частота знаков игрока и компьютера (числа, проценты или оба вида).

Логи работы (партии, сохранение раундов, ошибки БД) пишутся в `app.log`.

## Установка

Требуется Python 3.10+.

```bash
git clone <URL-репозитория>
cd rps-cli

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e .                 # только утилита
pip install -e ".[dev]"          # утилита + pytest и ruff
# либо: pip install -r requirements.txt && pip install -e .
```

## Использование

```bash
rps --help
rps play                # 3 раунда (по умолчанию)
rps play --rounds 5     # или -r 5
rps stats               # оба вида: 9 (45.0%)
rps stats --view abs    # только числа
rps stats --view rel    # только проценты
python -m rps stats     # запуск без установки скрипта
```

### Пример

```text
$ rps play -r 2
Раунд 1/2. Ваш выбор (rock, paper, scissors): rock
Вы: 🪨 rock   Компьютер: ✂️ scissors
Результат: вы выиграли! 🎉

Раунд 2/2. Ваш выбор (rock, paper, scissors): paper
Вы: 📄 paper   Компьютер: 📄 paper
Результат: ничья 🤝

Итоговый счёт — Игрок: 1, Компьютер: 0, Ничьи: 1
Вы победили в партии!

$ rps stats
Победы игрока: 9 (45.0%)
Победы компьютера: 8 (40.0%)
Ничьи: 3 (15.0%)
Игрок:     rock 7 (35.0%), paper 8 (40.0%), scissors 5 (25.0%)
Компьютер: rock 6 (30.0%), paper 6 (30.0%), scissors 8 (40.0%)
```

### Ошибки

Ожидаемые ошибки (неверный `--rounds`/`--view`, недоступная база или лог)
выводятся как `Error: ...` без traceback, код выхода — ненулевой
(`2` — неверные аргументы, `1` — прочие ошибки).

### Настройки

| Опция группы | Переменная окружения | По умолчанию |
|--------------|----------------------|--------------|
| `--db`       | `RPS_DB`             | `stats.db`   |
| `--log-file` | `RPS_LOG_FILE`       | `app.log`    |

```bash
rps --db my_game.db --log-file my.log stats
```

## Тесты и проверки

```bash
pytest                  # автотесты
ruff format --check .   # форматирование
ruff check .            # линтер
```

Тесты используют `sqlite:///:memory:` и временные каталоги, поэтому
не создают файлов в репозитории.

## Структура

```text
src/rps/
  cli.py             # Click-команды: только ввод/вывод
  logic.py           # бизнес-логика: determine_winner, Score, отчёт статистики
  db.py              # работа с SQLite: сессии, транзакции, запросы
  models.py          # модель Round (SQLAlchemy)
  logging_config.py  # логирование в app.log
tests/
  test_rps.py        # логика (все 9 комбинаций, граничные случаи)
  test_db.py         # база: агрегаты, откат при ошибке, файл на диске
  test_cli.py        # CLI: коды выхода, сообщения, логи
```
