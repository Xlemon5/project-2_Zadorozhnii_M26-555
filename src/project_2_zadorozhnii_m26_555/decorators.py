import time

from project_2_zadorozhnii_m26_555.constants import CONFIRMATION_RESPONSE


def _preserve_metadata(wrapper, function):
    """Сохраняет имя, документацию и исходную функцию без сторонних модулей."""
    for attribute in (
        "__name__",
        "__doc__",
        "__module__",
        "__qualname__",
        "__annotations__",
    ):
        if hasattr(function, attribute):
            setattr(wrapper, attribute, getattr(function, attribute))
    wrapper.__wrapped__ = function
    return wrapper


def _create_error_handler():
    """Создаёт общий счётчик вложенных операций однопоточной консоли."""
    depth = 0

    def handle_db_errors(function):
        """Перехватывает исключения на внешней границе операции базы данных."""

        def wrapper(*args, **kwargs):
            """Выводит ошибку один раз, не продолжая ошибочные вложенные вызовы."""
            nonlocal depth
            depth += 1
            try:
                return function(*args, **kwargs)
            except Exception as error:
                if depth > 1:
                    raise
                if isinstance(error, FileNotFoundError):
                    print(
                        "Ошибка: Файл данных не найден. "
                        "Возможно, база данных не инициализирована."
                    )
                elif isinstance(error, KeyError):
                    print(f"Ошибка: Таблица или столбец {error} не найден.")
                elif isinstance(error, ValueError):
                    print(getattr(error, "user_message", f"Ошибка валидации: {error}"))
                elif isinstance(error, OSError):
                    print(f"Ошибка работы с файлами: {error}")
                else:
                    print(f"Произошла непредвиденная ошибка: {error}")
                return None
            finally:
                depth -= 1

        return _preserve_metadata(wrapper, function)

    return handle_db_errors


handle_db_errors = _create_error_handler()


def confirm_action(action_name):
    """Создаёт декоратор подтверждения опасного действия ответом y."""

    def decorator(function):
        """Добавляет запрос подтверждения к выбранной функции."""

        def wrapper(*args, **kwargs):
            """Выполняет действие только после положительного ответа."""
            try:
                answer = input(
                    f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
                )
            except (EOFError, KeyboardInterrupt):
                print("\nОперация отменена.")
                return None
            if answer.strip() != CONFIRMATION_RESPONSE:
                print("Операция отменена.")
                return None
            return function(*args, **kwargs)

        return _preserve_metadata(wrapper, function)

    return decorator


def log_time(function):
    """Выводит длительность вызова функции по монотонным часам."""

    def wrapper(*args, **kwargs):
        """Сохраняет результат или исключение и печатает время выполнения."""
        started_at = time.monotonic()
        try:
            return function(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - started_at
            print(f"Функция {function.__name__} выполнилась за {elapsed:.3f} секунд.")

    return _preserve_metadata(wrapper, function)


def create_cacher():
    """Возвращает функцию с кэшем в замыкании и методом cache_clear."""
    cache = {}

    def cache_result(key, value_func):
        """Вычисляет значение только для ещё не сохранённого ключа."""
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    cache_result.cache_clear = cache.clear
    return cache_result
