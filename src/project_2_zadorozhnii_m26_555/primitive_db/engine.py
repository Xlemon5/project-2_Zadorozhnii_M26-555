import shlex

import prompt

from project_2_zadorozhnii_m26_555.primitive_db.core import create_table, drop_table
from project_2_zadorozhnii_m26_555.primitive_db.utils import (
    load_metadata,
    save_metadata,
)

METADATA_FILE = "db_meta.json"


def print_help() -> None:
    print("\n***База данных***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> ... - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")
    print("Поддерживаемые типы: int, str, bool.\n")


def run() -> None:
    print_help()

    while True:
        try:
            user_input = prompt.string(">>>Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            print()
            return

        try:
            arguments = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Проверьте кавычки.")
            continue

        if not arguments:
            continue

        command = arguments[0]
        match arguments:
            case ["exit"]:
                return
            case ["help"]:
                print_help()
                continue
            case ["create_table", _, *columns] if columns:
                pass
            case ["drop_table", _] | ["list_tables"]:
                pass
            case _:
                if command in {
                    "create_table",
                    "drop_table",
                    "list_tables",
                    "help",
                    "exit",
                }:
                    print(
                        f"Некорректное значение: {user_input}. "
                        "Введите help для справки."
                    )
                else:
                    print(f"Функции {command} нет. Попробуйте снова.")
                continue

        try:
            metadata = load_metadata(METADATA_FILE)
        except (OSError, ValueError) as error:
            print(f"Ошибка чтения метаданных: {error}")
            continue

        try:
            if command == "create_table":
                table_name = arguments[1]
                metadata = create_table(metadata, table_name, arguments[2:])
                save_metadata(METADATA_FILE, metadata)
                print(
                    f'Таблица "{table_name}" успешно создана со столбцами: '
                    f"{', '.join(metadata[table_name])}"
                )
            elif command == "drop_table":
                table_name = arguments[1]
                metadata = drop_table(metadata, table_name)
                save_metadata(METADATA_FILE, metadata)
                print(f'Таблица "{table_name}" успешно удалена.')
            elif metadata:
                for table_name in sorted(metadata):
                    print(f"- {table_name}")
            else:
                print("Таблиц пока нет.")
        except ValueError as error:
            print(error)
        except OSError as error:
            print(f"Ошибка сохранения метаданных: {error}")
