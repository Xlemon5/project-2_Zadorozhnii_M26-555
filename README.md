# Primitive DB

Учебное консольное приложение, имитирующее работу с базой данных.
На этапе подготовки реализованы запуск приложения и команды `help` и `exit`.
Управление зависимостями, виртуальным окружением и сборкой выполняется через uv.

## Требования

- Python 3.12 или новее; `.python-version` выбирает Python 3.12 для разработки.
- [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Make для запуска команд из `Makefile`.

## Установка и запуск

Из корня проекта выполните:

```bash
make install
make project
```

Эквивалентные команды без Make:

```bash
uv sync
uv run project
```

`uv sync` создаёт `.venv` в корне проекта и устанавливает пакет и зависимости,
включая Ruff из группы `dev`. Версии зависимостей зафиксированы в `uv.lock`.
Файл `uv.lock` нужно хранить в Git, а `.venv` и `dist` исключены через `.gitignore`.

Запуск модуля напрямую:

```bash
uv run python -m project_2_zadorozhnii_m26_555.primitive_db.main
```

После запуска приложение выводит `DB project is running!` и приглашение ко вводу.
Команда `help` повторяет справку, `exit` завершает работу.
Также выйти можно через Ctrl+C или Ctrl+D.

При использовании `uv run` активировать окружение вручную не требуется.
Чтобы запускать `project` без префикса `uv run` на macOS/Linux:

```bash
source .venv/bin/activate
project
```

## Команды разработки

| Команда | Действие |
| --- | --- |
| `make install` | Установка проекта и зависимостей через `uv sync` |
| `make project` | Запуск приложения через `uv run project` |
| `make lint` | Проверка кода через `uv run ruff check .` |
| `make build` | Сборка wheel и sdist в `dist/` через `uv build` |
| `make publish` | Сборка и пробная публикация через uv без загрузки в PyPI |
| `make package-install` | Сборка и установка wheel в существующее окружение `.venv` |

`make publish` выполняет `uv publish --dry-run --trusted-publishing never`.
Пакет не загружается в PyPI, поиск токена CI отключён для локальной проверки.
Перед `make package-install` выполните `make install`, чтобы создать окружение.
После установки wheel запустите `.venv/bin/project`, чтобы проверить установленный
пакет без повторной синхронизации исходников через `uv run`.

Добавление обычной зависимости и зависимости для разработки:

```bash
uv add prompt
uv add --dev ruff
```

Форматирование кода:

```bash
uv run ruff format .
```

## Структура

```text
src/
└── project_2_zadorozhnii_m26_555/
    ├── __init__.py
    └── primitive_db/
        ├── __init__.py
        ├── engine.py
        └── main.py
```

`main.py` содержит точку входа, а `engine.py` — приветствие и цикл команд.
Настройки пакета, консольной команды `project` и Ruff находятся в `pyproject.toml`.
Пакет собирается с помощью `uv_build`; секции `[tool.poetry]` не используются.
