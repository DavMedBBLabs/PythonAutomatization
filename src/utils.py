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


def request_json_file(path_env: str) -> str:
    """Prompt the user for a JSON file name and return the full path."""
    while True:
        file_name = input('Nombre del archivo JSON (sin extensión .json): ').strip()
        json_file = os.path.join(path_env, f'{file_name}.json')
        if verify_existing_file(json_file):
            break
    return json_file


def request_excel_file(path_env: str) -> str:
    """Prompt the user for an Excel file name and return the full path."""
    while True:
        file_name = input('Nombre del archivo Excel (sin extensión): ').strip()
        xlsx = os.path.join(path_env, f'{file_name}.xlsx')
        xls = os.path.join(path_env, f'{file_name}.xls')
        if verify_existing_file(xlsx):
            return xlsx
        if verify_existing_file(xls):
            return xls
    return ''


def confirm_action(message: str) -> bool:
    """Ask the user to confirm an action."""
    resp = input(f"{message} (s/N): ").strip().lower()
    return resp in ('s', 'si', 'y', 'yes')


def list_files(directory: str, extensions: tuple[str, ...]) -> list[str]:
    """Return and display files with given *extensions* in *directory*."""
    files = [f for f in os.listdir(directory) if f.lower().endswith(extensions)]
    if files:
        print('Archivos encontrados:')
        for name in files:
            print(f"- {name}")
    else:
        print('No se encontraron archivos.')
    return files
