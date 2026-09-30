import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from project_2_zadorozhnii_m26_555.primitive_db.core import validate_columns


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
