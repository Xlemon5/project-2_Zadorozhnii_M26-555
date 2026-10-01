import json
import shlex

from project_2_zadorozhnii_m26_555.constants import (
    ASSIGNMENT_LENGTH,
    ASSIGNMENT_STRIDE,
    DATA_COMMANDS,
    STRING_QUOTES,
    TABLE_COMMANDS,
    TOKEN_PUNCTUATION,
)
from project_2_zadorozhnii_m26_555.errors import command_error


def _read_quoted_token(text: str, position: int) -> tuple[str, int]:
    """Читает строковый токен с учётом экранированных кавычек."""
    quote = text[position]
    end = position + 1
    while end < len(text):
        if text[end] == "\\":
            end += 2
        elif text[end] == quote:
            return text[position : end + 1], end + 1
        else:
            end += 1
    raise command_error(f"Некорректное значение: {text}. Попробуйте снова.")


def tokenize(text: str) -> list[str]:
    """Разбивает команду на слова, знаки и строки, сохраняя кавычки."""
    tokens = []
    text = text.strip()
    position = 0
    while position < len(text):
        character = text[position]
        if character.isspace():
            position += 1
        elif character in STRING_QUOTES:
            token, position = _read_quoted_token(text, position)
            tokens.append(token)
        elif character in TOKEN_PUNCTUATION:
            tokens.append(character)
            position += 1
        elif character == "\\":
            raise command_error(f"Некорректное значение: {text}. Попробуйте снова.")
        else:
            start = position
            while (
                position < len(text)
                and not text[position].isspace()
                and text[position] not in TOKEN_PUNCTUATION + STRING_QUOTES + "\\"
            ):
                position += 1
            tokens.append(text[start:position])
    return tokens


def _parse_string(token: str) -> str:
    """Преобразует строку в кавычках через JSON, не исполняя Python-код."""
    _, end = _read_quoted_token(token, 0)
    if end != len(token):
        raise command_error(f"Некорректное значение: {token}. Попробуйте снова.")
    encoded = ['"']
    position = 1
    while position < len(token) - 1:
        character = token[position]
        if character == "\\":
            escaped = token[position + 1]
            encoded.append("'" if escaped == "'" else "\\" + escaped)
            position += 2
        else:
            encoded.append('\\"' if character == '"' else character)
            position += 1
    encoded.append('"')
    try:
        return json.loads("".join(encoded))
    except ValueError as error:
        raise command_error(
            f"Некорректное значение: {token}. Попробуйте снова."
        ) from error


def parse_value(token: str) -> int | str | bool:
    """Разбирает целое число, true/false или строку в кавычках."""
    if token in {"true", "false"}:
        return token == "true"
    digits = token[1:] if token.startswith(("+", "-")) else token
    if digits and digits.isdecimal():
        return int(token)
    if token and token[0] in STRING_QUOTES:
        return _parse_string(token)
    raise command_error(f"Некорректное значение: {token}. Попробуйте снова.")


def _parse_assignments(tokens: list[str]) -> dict:
    """Собирает словарь присваиваний, разделённых запятыми."""
    if len(tokens) % ASSIGNMENT_STRIDE != ASSIGNMENT_LENGTH:
        raise ValueError("Некорректное условие. Ожидается столбец = значение.")
    result = {}
    for position in range(0, len(tokens), ASSIGNMENT_STRIDE):
        boundary = position + ASSIGNMENT_LENGTH
        column, operator, value = tokens[position:boundary]
        if not column.isidentifier() or operator != "=" or column in result:
            raise ValueError("Некорректное условие или повторяющийся столбец.")
        if boundary < len(tokens) and tokens[boundary] != ",":
            raise ValueError("Присваивания в set должны разделяться запятыми.")
        result[column] = parse_value(value)
    return result


def parse_where(text: str) -> dict:
    """Разбирает одно условие равенства для where."""
    tokens = tokenize(text)
    if len(tokens) != ASSIGNMENT_LENGTH:
        raise ValueError("В where требуется одно условие: столбец = значение.")
    return _parse_assignments(tokens)


def parse_set(text: str) -> dict:
    """Разбирает одно или несколько присваиваний для set."""
    return _parse_assignments(tokenize(text))


def parse_command(user_input: str) -> dict:
    """Возвращает команду с аргументами или сообщает об ошибке синтаксиса."""
    words = user_input.split(maxsplit=1)
    if not words:
        return {"command": ""}
    command = words[0]
    if command not in TABLE_COMMANDS | DATA_COMMANDS:
        raise command_error(f"Функции {command} нет. Попробуйте снова.")

    if command in TABLE_COMMANDS:
        try:
            arguments = shlex.split(user_input)
        except ValueError as error:
            raise command_error(
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
                boundary = ASSIGNMENT_LENGTH
                while boundary < len(assignments) and assignments[boundary] == ",":
                    boundary += ASSIGNMENT_STRIDE
                if boundary < len(assignments) and assignments[boundary] == "where":
                    return {
                        "command": command,
                        "table_name": table_name,
                        "set": parse_set(" ".join(assignments[:boundary])),
                        "where": parse_where(" ".join(assignments[boundary + 1 :])),
                    }
            case ["info", table_name]:
                return {"command": command, "table_name": table_name}

    raise command_error(f"Некорректное значение: {user_input}. Попробуйте снова.")
