import time
from contextvars import ContextVar
from functools import wraps

from project_2_zadorozhnii_m26_555.errors import CommandError

_handling_db_errors = ContextVar("handling_db_errors", default=False)


def handle_db_errors(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        nested = _handling_db_errors.get()
        token = _handling_db_errors.set(True)
        try:
            return function(*args, **kwargs)
        except Exception as error:
            if nested:
                raise
            if isinstance(error, FileNotFoundError):
                print(
                    "Ошибка: Файл данных не найден. "
                    "Возможно, база данных не инициализирована."
                )
            elif isinstance(error, KeyError):
                print(f"Ошибка: Таблица или столбец {error} не найден.")
            elif isinstance(error, CommandError):
                print(error)
            elif isinstance(error, ValueError):
                print(f"Ошибка валидации: {error}")
            elif isinstance(error, OSError):
                print(f"Ошибка работы с файлами: {error}")
            else:
                print(f"Произошла непредвиденная ошибка: {error}")
            return None
        finally:
            _handling_db_errors.reset(token)

    return wrapper


def confirm_action(action_name):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                answer = input(
                    f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
                )
            except (EOFError, KeyboardInterrupt):
                print("\nОперация отменена.")
                return None
            if answer.strip() != "y":
                print("Операция отменена.")
                return None
            return function(*args, **kwargs)

        return wrapper

    return decorator


def log_time(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        started_at = time.monotonic()
        try:
            return function(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - started_at
            print(f"Функция {function.__name__} выполнилась за {elapsed:.3f} секунд.")

    return wrapper


def create_cacher():
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    cache_result.cache_clear = cache.clear
    return cache_result
