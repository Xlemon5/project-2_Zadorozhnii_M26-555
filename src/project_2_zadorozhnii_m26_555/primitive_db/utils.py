import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from project_2_zadorozhnii_m26_555.errors import CommandError

COLUMN_TYPES = {"int": int, "str": str, "bool": bool}


def validate_columns(columns: list[str]) -> list[str]:
    if not columns:
        raise CommandError(
            "Некорректное значение: пустой список столбцов. Попробуйте снова."
        )

    result = ["ID:int"]
    column_names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise CommandError(f"Некорректное значение: {column}. Попробуйте снова.")

        name, data_type = parts
        if (
            not name.isidentifier()
            or data_type not in COLUMN_TYPES
            or name in column_names
            or (name == "ID" and data_type != "int")
        ):
            raise CommandError(f"Некорректное значение: {column}. Попробуйте снова.")

        column_names.add(name)
        if name != "ID":
            result.append(column)

    return result


def load_metadata(filepath: str | Path) -> dict[str, list[str]]:
    try:
        with open(filepath, encoding="utf-8") as metadata_file:
            data = json.load(metadata_file)
    except FileNotFoundError:
        return {}

    if not isinstance(data, dict):
        raise ValueError("Метаданные должны быть объектом JSON.")
    for table_name, columns in data.items():
        if (
            not table_name.isidentifier()
            or not isinstance(columns, list)
            or not all(isinstance(column, str) for column in columns)
            or columns != validate_columns(columns)
        ):
            raise ValueError(f'Некорректная структура таблицы "{table_name}".')

    return data


def save_metadata(filepath: str | Path, data: dict[str, list[str]]) -> None:
    _save_json(filepath, data)


def table_data_path(table_name: str) -> Path:
    if not table_name.isidentifier():
        raise CommandError(f"Некорректное значение: {table_name}. Попробуйте снова.")
    return Path("data") / f"{table_name}.json"


def load_table_data(table_name: str) -> list[dict]:
    try:
        with table_data_path(table_name).open(encoding="utf-8") as table_file:
            data = json.load(table_file)
    except FileNotFoundError:
        return []

    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError(f'Некорректные данные таблицы "{table_name}".')
    return data


def save_table_data(table_name: str, data: list[dict]) -> None:
    filepath = table_data_path(table_name)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    _save_json(filepath, data)


def delete_table_data(table_name: str) -> None:
    table_data_path(table_name).unlink(missing_ok=True)


def _save_json(filepath: str | Path, data: dict | list) -> None:
    filepath = Path(filepath)
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=filepath.parent,
            prefix=f".{filepath.name}.",
            suffix=".tmp",
            delete=False,
        ) as metadata_file:
            temporary_path = Path(metadata_file.name)
            json.dump(data, metadata_file, ensure_ascii=False, indent=2)
            metadata_file.write("\n")
        temporary_path.replace(filepath)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
