import json

import prompt
from prettytable import PrettyTable

from project_2_zadorozhnii_m26_555.constants import (
    ID_COLUMN,
    INPUT_PROMPT,
    METADATA_FILE,
)
from project_2_zadorozhnii_m26_555.decorators import create_cacher, handle_db_errors
from project_2_zadorozhnii_m26_555.primitive_db.core import (
    create_table,
    delete,
    drop_table,
    get_schema,
    insert,
    select,
    update,
    validate_clause,
    validate_table_data,
)
from project_2_zadorozhnii_m26_555.primitive_db.parser import parse_command
from project_2_zadorozhnii_m26_555.primitive_db.utils import (
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

_select_cache = create_cacher()


def print_help() -> None:
    """Печатает все команды управления таблицами и данными."""
    print("\n***База данных***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> ... - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("\n***Операции с данными***")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> "
        "- прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация")
    print("Типы: int, str, bool. Строки вводите в кавычках, bool — true/false.\n")
    print("Удаление таблиц и записей требует подтверждения: y.\n")


def print_rows(schema: dict[str, type], rows: list[dict]) -> None:
    """Выводит записи через PrettyTable в порядке столбцов схемы."""
    table = PrettyTable()
    table.field_names = list(schema)
    table.add_rows([[row[column] for column in schema] for row in rows])
    print(table)


@handle_db_errors
def select_cached(
    table_name: str, table_data: list[dict], where_clause: dict | None = None
) -> list[dict]:
    """Возвращает изолированную копию кэшированной выборки таблицы."""
    key = (
        table_name,
        json.dumps(where_clause, sort_keys=True, ensure_ascii=False),
        json.dumps(table_data, sort_keys=True, ensure_ascii=False),
    )
    rows = _select_cache(key, lambda: select(table_data, where_clause))
    return [row.copy() for row in rows]


@handle_db_errors
def execute_command(metadata: dict[str, list[str]], request: dict) -> None:
    """Выполняет разобранную команду, сохраняет изменения и обновляет кэш."""
    command = request["command"]
    if command == "list_tables":
        if metadata:
            for table_name in sorted(metadata):
                print(f"- {table_name}")
        else:
            print("Таблиц пока нет.")
        return

    table_name = request["table_name"]
    if command == "create_table":
        metadata = create_table(metadata, table_name, request["columns"])
        save_table_data(table_name, [])
        save_metadata(METADATA_FILE, metadata)
        _select_cache.cache_clear()
        print(
            f'Таблица "{table_name}" успешно создана со столбцами: '
            f"{', '.join(metadata[table_name])}"
        )
        return
    if command == "drop_table":
        get_schema(metadata, table_name)
        metadata = drop_table(metadata, table_name)
        if metadata is None:
            return
        save_metadata(METADATA_FILE, metadata)
        _select_cache.cache_clear()
        try:
            delete_table_data(table_name)
        except OSError as error:
            print(f"Не удалось удалить файл данных: {error}")
        print(f'Таблица "{table_name}" успешно удалена.')
        return

    schema = get_schema(metadata, table_name)
    table_data = load_table_data(table_name)
    validate_table_data(schema, table_data)

    where_clause = request.get("where")
    if where_clause is not None:
        validate_clause(schema, where_clause)

    if command == "insert":
        table_data = insert(metadata, table_name, request["values"], table_data)
        save_table_data(table_name, table_data)
        _select_cache.cache_clear()
        print(
            f"Запись с ID={table_data[-1][ID_COLUMN]} "
            f'успешно добавлена в таблицу "{table_name}".'
        )
    elif command == "select":
        print_rows(schema, select_cached(table_name, table_data, where_clause))
    elif command == "info":
        print(f"Таблица: {table_name}")
        print(f"Столбцы: {', '.join(metadata[table_name])}")
        print(f"Количество записей: {len(table_data)}")
    else:
        matched_rows = select_cached(table_name, table_data, where_clause)
        if command == "update":
            validate_clause(schema, request["set"])
            table_data = update(table_data, request["set"], where_clause)
        else:
            if not matched_rows:
                print("Подходящих записей не найдено.")
                return
            table_data = delete(table_data, where_clause)
            if table_data is None:
                return
        if not matched_rows:
            print("Подходящих записей не найдено.")
            return
        save_table_data(table_name, table_data)
        _select_cache.cache_clear()
        for row in matched_rows:
            if command == "update":
                print(
                    f'Запись с ID={row[ID_COLUMN]} в таблице "{table_name}" '
                    "успешно обновлена."
                )
            else:
                print(
                    f"Запись с ID={row[ID_COLUMN]} успешно удалена "
                    f'из таблицы "{table_name}".'
                )


@handle_db_errors
def process_command(user_input: str) -> bool:
    """Обрабатывает ввод; False завершает цикл, ошибка возвращает None."""
    request = parse_command(user_input)
    command = request["command"]
    if not command:
        return True
    if command == "exit":
        return False
    if command == "help":
        print_help()
        return True

    metadata = load_metadata(METADATA_FILE)
    execute_command(metadata, request)
    return True


def run() -> None:
    """Запускает консольный цикл до команды exit, EOF или Ctrl+C."""
    print_help()

    while True:
        try:
            user_input = prompt.string(INPUT_PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if process_command(user_input) is False:
            return
