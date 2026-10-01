def command_error(message: str) -> ValueError:
    """Создаёт стандартное исключение с готовым сообщением для консоли."""
    error = ValueError(message)
    error.user_message = message
    return error
