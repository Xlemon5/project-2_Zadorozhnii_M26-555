from project_2_zadorozhnii_m26_555.primitive_db.utils import (
    COLUMN_TYPES,
    load_table_data,
    validate_columns,
)


def create_table(
    metadata: dict[str, list[str]], table_name: str, columns: list[str]
) -> dict[str, list[str]]:
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное значение: {table_name}. Попробуйте снова.")
    if table_name in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" уже существует.')

    metadata[table_name] = validate_columns(columns)
    return metadata


def drop_table(metadata: dict[str, list[str]], table_name: str) -> dict[str, list[str]]:
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')

    del metadata[table_name]
    return metadata


def get_schema(metadata: dict[str, list[str]], table_name: str) -> dict[str, type]:
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')
    return {
        name: COLUMN_TYPES[data_type]
        for name, data_type in (column.split(":") for column in metadata[table_name])
    }


def validate_clause(schema: dict[str, type], clause: dict) -> None:
    for column, value in clause.items():
        if column not in schema:
            raise ValueError(f'Ошибка: Столбец "{column}" не существует.')
        if type(value) is not schema[column]:
            raise ValueError(
                f"Некорректное значение: {value!r}. "
                f'Столбец "{column}" требует тип {schema[column].__name__}.'
            )


def validate_table_data(schema: dict[str, type], table_data: list[dict]) -> None:
    identifiers = set()
    for row in table_data:
        if set(row) != set(schema):
            raise ValueError("Данные таблицы не соответствуют структуре столбцов.")
        validate_clause(schema, row)
        if row["ID"] <= 0 or row["ID"] in identifiers:
            raise ValueError("ID записей должны быть положительными и уникальными.")
        identifiers.add(row["ID"])


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


def select(table_data: list[dict], where_clause: dict | None = None) -> list[dict]:
    if where_clause is None:
        return list(table_data)
    _validate_row_clauses(table_data, where_clause)
    return [row for row in table_data if _matches(row, where_clause)]


def update(table_data: list[dict], set_clause: dict, where_clause: dict) -> list[dict]:
    if "ID" in set_clause:
        raise ValueError("Ошибка: Столбец ID изменять нельзя.")
    _validate_row_clauses(table_data, set_clause, where_clause)
    for row in table_data:
        if _matches(row, where_clause):
            row.update(set_clause)
    return table_data


def delete(table_data: list[dict], where_clause: dict) -> list[dict]:
    _validate_row_clauses(table_data, where_clause)
    return [row for row in table_data if not _matches(row, where_clause)]
