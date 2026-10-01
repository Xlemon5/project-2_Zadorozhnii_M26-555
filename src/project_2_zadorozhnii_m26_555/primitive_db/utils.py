import json
import os

from project_2_zadorozhnii_m26_555.constants import (
    COLUMN_TYPES,
    DATA_DIRECTORY,
    FILE_ENCODING,
    ID_COLUMN,
    ID_DEFINITION,
    JSON_INDENT,
    TEMP_NAME_BYTES,
)
from project_2_zadorozhnii_m26_555.errors import command_error


def validate_columns(columns: list[str]) -> list[str]:
    """Проверяет определения столбцов и помещает единственный ID первым."""
    if not columns:
        raise command_error(
            "Некорректное значение: пустой список столбцов. Попробуйте снова."
        )

    result = [ID_DEFINITION]
    column_names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise command_error(f"Некорректное значение: {column}. Попробуйте снова.")

        name, data_type = parts
        if (
            not name.isidentifier()
            or data_type not in COLUMN_TYPES
            or name in column_names
            or (name == ID_COLUMN and data_type != "int")
        ):
            raise command_error(f"Некорректное значение: {column}. Попробуйте снова.")

        column_names.add(name)
        if name != ID_COLUMN:
            result.append(column)

    return result


def load_metadata(filepath: str | os.PathLike) -> dict[str, list[str]]:
    """Загружает и проверяет схему; отсутствие файла означает пустую базу."""
    try:
        with open(filepath, encoding=FILE_ENCODING) as metadata_file:
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


def save_metadata(filepath: str | os.PathLike, data: dict[str, list[str]]) -> None:
    """Атомарно сохраняет метаданные таблиц в JSON."""
    _save_json(filepath, data)


def table_data_path(table_name: str) -> str:
    """Возвращает путь данных, запрещая выход за пределы их директории."""
    if not table_name.isidentifier():
        raise command_error(f"Некорректное значение: {table_name}. Попробуйте снова.")
    return os.path.join(DATA_DIRECTORY, f"{table_name}.json")


def load_table_data(table_name: str) -> list[dict]:
    """Читает записи таблицы, возвращая пустой список при отсутствии файла."""
    try:
        with open(table_data_path(table_name), encoding=FILE_ENCODING) as table_file:
            data = json.load(table_file)
    except FileNotFoundError:
        return []

    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError(f'Некорректные данные таблицы "{table_name}".')
    return data


def save_table_data(table_name: str, data: list[dict]) -> None:
    """Создаёт директорию данных и атомарно сохраняет записи таблицы."""
    filepath = table_data_path(table_name)
    os.makedirs(DATA_DIRECTORY, exist_ok=True)
    _save_json(filepath, data)


def delete_table_data(table_name: str) -> None:
    """Удаляет файл таблицы; отсутствие файла не считается ошибкой."""
    _remove_file(table_data_path(table_name))


def _remove_file(filepath: str | os.PathLike) -> None:
    """Удаляет существующий файл, игнорируя только FileNotFoundError."""
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass


def _save_json(filepath: str | os.PathLike, data: dict | list) -> None:
    """Записывает временный JSON рядом с целевым файлом и заменяет оригинал."""
    filepath = os.fspath(filepath)
    while True:
        suffix = os.urandom(TEMP_NAME_BYTES).hex()
        temporary_path = os.path.join(
            os.path.dirname(filepath), f".{os.path.basename(filepath)}.{suffix}.tmp"
        )
        try:
            temporary_file = open(temporary_path, "x", encoding=FILE_ENCODING)
        except FileExistsError:
            continue
        break
    try:
        with temporary_file:
            json.dump(data, temporary_file, ensure_ascii=False, indent=JSON_INDENT)
            temporary_file.write("\n")
        os.replace(temporary_path, filepath)
    finally:
        _remove_file(temporary_path)
