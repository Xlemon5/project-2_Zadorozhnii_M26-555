import prompt
from prettytable import PrettyTable

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
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
    table_data_path,
)

METADATA_FILE = "db_meta.json"


def print_help() -> None:
    print("\n***База данных***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> ... - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("\n***Операции с данными***")
    print("<command> insert into <таблица> values (<значение1>, ...) - создать запись")
    print("<command> select from <таблица> - прочитать все записи")
    print(
        "<command> select from <таблица> where <столбец> = <значение> - отбор записей"
    )
    print(
        "<command> update <таблица> set <столбец> = <значение> "
        "where <столбец> = <значение> - обновить записи"
    )
    print(
        "<command> delete from <таблица> where <столбец> = <значение> - удалить записи"
    )
    print("<command> info <таблица> - информация о таблице")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")
    print("Типы: int, str, bool. Строки вводите в кавычках, bool — true/false.\n")


def print_rows(schema: dict[str, type], rows: list[dict]) -> None:
    table = PrettyTable()
    table.field_names = list(schema)
    table.add_rows([[row[column] for column in schema] for row in rows])
    print(table)


def execute_command(metadata: dict[str, list[str]], request: dict) -> None:
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
        print(
            f'Таблица "{table_name}" успешно создана со столбцами: '
            f"{', '.join(metadata[table_name])}"
        )
        return
    if command == "drop_table":
        metadata = drop_table(metadata, table_name)
        save_metadata(METADATA_FILE, metadata)
        try:
            table_data_path(table_name).unlink(missing_ok=True)
        except OSError as error:
            print(f"Не удалось удалить файл данных: {error}")
        print(f'Таблица "{table_name}" успешно удалена.')
        return

    schema = get_schema(metadata, table_name)
    try:
        table_data = load_table_data(table_name)
        validate_table_data(schema, table_data)
    except (OSError, ValueError) as error:
        raise ValueError(
            f'Ошибка чтения данных таблицы "{table_name}": {error}'
        ) from error

    where_clause = request.get("where")
    if where_clause is not None:
        validate_clause(schema, where_clause)

    if command == "insert":
        table_data = insert(metadata, table_name, request["values"], table_data)
        save_table_data(table_name, table_data)
        print(
            f"Запись с ID={table_data[-1]['ID']} "
            f'успешно добавлена в таблицу "{table_name}".'
        )
    elif command == "select":
        print_rows(schema, select(table_data, where_clause))
    elif command == "info":
        print(f"Таблица: {table_name}")
        print(f"Столбцы: {', '.join(metadata[table_name])}")
        print(f"Количество записей: {len(table_data)}")
    else:
        matched_rows = select(table_data, where_clause)
        if command == "update":
            validate_clause(schema, request["set"])
            table_data = update(table_data, request["set"], where_clause)
        else:
            table_data = delete(table_data, where_clause)
        if not matched_rows:
            print("Подходящих записей не найдено.")
            return
        save_table_data(table_name, table_data)
        for row in matched_rows:
            if command == "update":
                print(
                    f'Запись с ID={row["ID"]} в таблице "{table_name}" '
                    "успешно обновлена."
                )
            else:
                print(
                    f"Запись с ID={row['ID']} успешно удалена "
                    f'из таблицы "{table_name}".'
                )


def run() -> None:
    print_help()

    while True:
        try:
            user_input = prompt.string(">>>Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            print()
            return

        try:
            request = parse_command(user_input)
        except ValueError as error:
            print(error)
            continue

        command = request["command"]
        if not command:
            continue
        if command == "exit":
            return
        if command == "help":
            print_help()
            continue

        try:
            metadata = load_metadata(METADATA_FILE)
        except (OSError, ValueError) as error:
            print(f"Ошибка чтения метаданных: {error}")
            continue

        try:
            execute_command(metadata, request)
        except ValueError as error:
            print(error)
        except OSError as error:
            print(f"Ошибка работы с файлами: {error}")
