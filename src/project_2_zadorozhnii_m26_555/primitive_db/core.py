SUPPORTED_TYPES = {"int", "str", "bool"}


def validate_columns(columns: list[str]) -> list[str]:
    if not columns:
        raise ValueError(
            "Некорректное значение: пустой список столбцов. Попробуйте снова."
        )

    result = ["ID:int"]
    column_names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")

        name, data_type = parts
        if (
            not name.isidentifier()
            or data_type not in SUPPORTED_TYPES
            or name in column_names
            or (name == "ID" and data_type != "int")
        ):
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")

        column_names.add(name)
        if name != "ID":
            result.append(column)

    return result


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
