import os
import time


def decorator_line() -> None:
    print('   ------------------------------------------------   ')


def wait_for(seconds: int) -> None:
    time.sleep(seconds)


def clean_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


def verify_existing_file(path_file: str) -> bool:
    if not os.path.isfile(path_file):
        decorator_line()
        print(f"Archivo '{path_file}' no encontrado. Intente de nuevo.")
        decorator_line()
        wait_for(2)
        clean_screen()
        return False
    return True


def request_file_name(path_env: str) -> str:
    while True:
        file_name = input('Nombre del archivo (sin extensión .csv): ').strip()
        input_file = os.path.join(path_env, f'{file_name}.csv')
        if verify_existing_file(input_file):
            break
    return f'{file_name}.csv'
