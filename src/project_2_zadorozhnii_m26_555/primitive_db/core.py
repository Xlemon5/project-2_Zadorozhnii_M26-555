from project_2_zadorozhnii_m26_555.decorators import (
    confirm_action,
    handle_db_errors,
    log_time,
)
from project_2_zadorozhnii_m26_555.errors import CommandError
from project_2_zadorozhnii_m26_555.primitive_db.utils import (
    COLUMN_TYPES,
    load_table_data,
    validate_columns,
)


@handle_db_errors
def create_table(
    metadata: dict[str, list[str]], table_name: str, columns: list[str]
) -> dict[str, list[str]]:
    if not table_name.isidentifier():
        raise CommandError(f"Некорректное значение: {table_name}. Попробуйте снова.")
    if table_name in metadata:
        raise CommandError(f'Ошибка: Таблица "{table_name}" уже существует.')

    metadata[table_name] = validate_columns(columns)
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata: dict[str, list[str]], table_name: str) -> dict[str, list[str]]:
    if table_name not in metadata:
        raise CommandError(f'Ошибка: Таблица "{table_name}" не существует.')

    del metadata[table_name]
    return metadata


@handle_db_errors
def get_schema(metadata: dict[str, list[str]], table_name: str) -> dict[str, type]:
    if table_name not in metadata:
        raise CommandError(f'Ошибка: Таблица "{table_name}" не существует.')
    return {
        name: COLUMN_TYPES[data_type]
        for name, data_type in (column.split(":") for column in metadata[table_name])
    }


@handle_db_errors
def validate_clause(schema: dict[str, type], clause: dict) -> None:
    for column, value in clause.items():
        if column not in schema:
            raise KeyError(column)
        if type(value) is not schema[column]:
            raise CommandError(f"Некорректное значение: {value}. Попробуйте снова.")


@handle_db_errors
def validate_table_data(schema: dict[str, type], table_data: list[dict]) -> None:
    identifiers = set()
    for row in table_data:
        if set(row) != set(schema):
            raise ValueError("Данные таблицы не соответствуют структуре столбцов.")
        validate_clause(schema, row)
        if row["ID"] <= 0 or row["ID"] in identifiers:
            raise ValueError("ID записей должны быть положительными и уникальными.")
        identifiers.add(row["ID"])


@handle_db_errors
@log_time
def insert(
    metadata: dict[str, list[str]],
    table_name: str,
    values: list,
    table_data: list[dict] | None = None,
) -> list[dict]:
    schema = get_schema(metadata, table_name)
    columns = [column for column in schema if column != "ID"]
    if len(values) != len(columns):
        raise ValueError(
            f"Некорректное количество значений: {len(values)}. "
            f"Ожидается {len(columns)} без ID."
        )
    record = dict(zip(columns, values))
    validate_clause(schema, record)
    if table_data is None:
        table_data = load_table_data(table_name)
    validate_table_data(schema, table_data)
    identifier = max((row["ID"] for row in table_data), default=0) + 1
    table_data.append({"ID": identifier, **record})
    return table_data


def _validate_row_clauses(table_data: list[dict], *clauses: dict) -> None:
    for row in table_data:
        schema = {column: type(value) for column, value in row.items()}
        for clause in clauses:
            validate_clause(schema, clause)


def _matches(row: dict, where_clause: dict) -> bool:
    return all(
        type(row[column]) is type(value) and row[column] == value
        for column, value in where_clause.items()
    )


@handle_db_errors
@log_time
def select(table_data: list[dict], where_clause: dict | None = None) -> list[dict]:
    if where_clause is not None:
        _validate_row_clauses(table_data, where_clause)
    return [
        row.copy()
        for row in table_data
        if where_clause is None or _matches(row, where_clause)
    ]


@handle_db_errors
def update(table_data: list[dict], set_clause: dict, where_clause: dict) -> list[dict]:
    if "ID" in set_clause:
        raise ValueError("Столбец ID изменять нельзя.")
    _validate_row_clauses(table_data, set_clause, where_clause)
    for row in table_data:
        if _matches(row, where_clause):
            row.update(set_clause)
    return table_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data: list[dict], where_clause: dict) -> list[dict]:
    _validate_row_clauses(table_data, where_clause)
    return [row for row in table_data if not _matches(row, where_clause)]
