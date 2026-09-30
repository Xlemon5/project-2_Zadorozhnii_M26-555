import prompt


def print_help() -> None:
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")


def welcome() -> None:
    print("DB project is running!")
    print("\n***")
    print_help()

    while True:
        try:
            command = prompt.string("Введите команду: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if command == "exit":
            return
        if command == "help":
            print_help()
        elif command:
            print("Неизвестная команда. Введите help для справки.")
