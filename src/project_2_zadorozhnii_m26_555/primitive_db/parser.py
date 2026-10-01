import ast
import re
import shlex

from project_2_zadorozhnii_m26_555.errors import CommandError

TOKEN_PATTERN = re.compile(
    r"""\s*("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[(),=]|[^\s(),="'\\]+)"""
)
TABLE_COMMANDS = {"create_table", "drop_table", "list_tables", "help", "exit"}
DATA_COMMANDS = {"insert", "select", "update", "delete", "info"}


def tokenize(text: str) -> list[str]:
    tokens = []
    text = text.strip()
    position = 0
    while position < len(text):
        match = TOKEN_PATTERN.match(text, position)
        if match is None:
            raise CommandError(f"Некорректное значение: {text}. Попробуйте снова.")
        tokens.append(match.group(1))
        position = match.end()
    return tokens


def parse_value(token: str) -> int | str | bool:
    if token in {"true", "false"}:
        return token == "true"
    if re.fullmatch(r"[+-]?\d+", token):
        return int(token)
    if token.startswith(('"', "'")):
        try:
            value = ast.literal_eval(token)
        except (ValueError, SyntaxError) as error:
            raise CommandError(
                f"Некорректное значение: {token}. Попробуйте снова."
            ) from error
        if isinstance(value, str):
            return value
    raise CommandError(f"Некорректное значение: {token}. Попробуйте снова.")


def _parse_assignments(tokens: list[str]) -> dict:
    if len(tokens) % 4 != 3:
        raise ValueError("Некорректное условие. Ожидается столбец = значение.")
    result = {}
    for position in range(0, len(tokens), 4):
        column, operator, value = tokens[position : position + 3]
        if not column.isidentifier() or operator != "=" or column in result:
            raise ValueError("Некорректное условие или повторяющийся столбец.")
        if position + 3 < len(tokens) and tokens[position + 3] != ",":
            raise ValueError("Присваивания в set должны разделяться запятыми.")
        result[column] = parse_value(value)
    return result


def parse_where(text: str) -> dict:
    tokens = tokenize(text)
    if len(tokens) != 3:
        raise ValueError("В where требуется одно условие: столбец = значение.")
    return _parse_assignments(tokens)


def parse_set(text: str) -> dict:
    return _parse_assignments(tokenize(text))


def parse_command(user_input: str) -> dict:
    words = user_input.split(maxsplit=1)
    if not words:
        return {"command": ""}
    command = words[0]
    if command not in TABLE_COMMANDS | DATA_COMMANDS:
        raise CommandError(f"Функции {command} нет. Попробуйте снова.")

    if command in TABLE_COMMANDS:
        try:
            arguments = shlex.split(user_input)
        except ValueError as error:
            raise CommandError(
                f"Некорректное значение: {user_input}. Попробуйте снова."
            ) from error
        match arguments:
            case ["help"] | ["exit"] | ["list_tables"]:
                return {"command": command}
            case ["create_table", table_name, *columns] if columns:
                return {
                    "command": command,
                    "table_name": table_name,
                    "columns": columns,
                }
            case ["drop_table", table_name]:
                return {"command": command, "table_name": table_name}
    else:
        arguments = tokenize(user_input)
        match arguments:
            case ["insert", "into", table_name, "values", "(", *values, ")"]:
                if values and (
                    len(values) % 2 == 0 or any(token != "," for token in values[1::2])
                ):
                    raise ValueError("Значения в values должны разделяться запятыми.")
                return {
                    "command": command,
                    "table_name": table_name,
                    "values": [parse_value(value) for value in values[::2]],
                }
            case ["select", "from", table_name]:
                return {"command": command, "table_name": table_name, "where": None}
            case ["select" | "delete", "from", table_name, "where", *condition]:
                return {
                    "command": command,
                    "table_name": table_name,
                    "where": parse_where(" ".join(condition)),
                }
            case ["update", table_name, "set", *assignments]:
                boundary = 3
                while boundary < len(assignments) and assignments[boundary] == ",":
                    boundary += 4
                if boundary < len(assignments) and assignments[boundary] == "where":
                    return {
                        "command": command,
                        "table_name": table_name,
                        "set": parse_set(" ".join(assignments[:boundary])),
                        "where": parse_where(" ".join(assignments[boundary + 1 :])),
                    }
            case ["info", table_name]:
                return {"command": command, "table_name": table_name}

    raise CommandError(f"Некорректное значение: {user_input}. Попробуйте снова.")
