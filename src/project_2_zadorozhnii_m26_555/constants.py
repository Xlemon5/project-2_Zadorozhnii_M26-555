"""Общие настройки хранения, типов данных и синтаксиса команд."""

METADATA_FILE = "db_meta.json"
DATA_DIRECTORY = "data"
FILE_ENCODING = "utf-8"
JSON_INDENT = 2
TEMP_NAME_BYTES = 8

COLUMN_TYPES = {"int": int, "str": str, "bool": bool}
ID_COLUMN = "ID"
ID_DEFINITION = "ID:int"

TABLE_COMMANDS = {"create_table", "drop_table", "list_tables", "help", "exit"}
DATA_COMMANDS = {"insert", "select", "update", "delete", "info"}
TOKEN_PUNCTUATION = "(),="
STRING_QUOTES = "\"'"
ASSIGNMENT_LENGTH = 3
ASSIGNMENT_STRIDE = ASSIGNMENT_LENGTH + 1
INPUT_PROMPT = ">>>Введите команду: "
CONFIRMATION_RESPONSE = "y"
