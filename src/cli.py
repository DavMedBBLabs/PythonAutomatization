import os
from dataclasses import asdict

from . import config
from .utils import clean_screen, wait_for, request_file_name
from .xray import get_token, send_json_to_xray
from .test_generator import generate_tests_json


def get_configuration() -> config.Config:
    input_csv = request_file_name(config.env_path())
    project_key = input('Clave de proyecto por defecto: ').strip()
    endpoint_url = os.getenv('XRAY_IMPORT_URL', 'https://xray.cloud.getxray.app/api/v1/import/test/bulk')
    token = get_token()
    output_json = f"{os.path.splitext(input_csv)[0]}.json"
    return config.Config(input_csv, project_key, token, endpoint_url, output_json)


def interactive_menu():
    clean_screen()
    cfg = get_configuration()

    while True:
        print('\n--- Menú Xray CSV->JSON -> API ---')
        print(f"1. Cambiar CSV de entrada (actual: {cfg.input_csv})")
        print(f"2. Cambiar project key (actual: {cfg.project_key})")
        print('3. Regenerar token de autenticación')
        print('4. Generar JSON')
        print('5. Enviar JSON a Xray')
        print('6. Salir')
        choice = input('Seleccione una opción: ').strip()

        if choice == '1':
            cfg.input_csv = request_file_name(config.env_path())
            cfg.output_json = f"{os.path.splitext(cfg.input_csv)[0]}.json"
        elif choice == '2':
            cfg.project_key = input('Nueva project key: ').strip()
        elif choice == '3':
            cfg.token = get_token()
            print('Token actualizado.')
        elif choice == '4':
            generate_tests_json(cfg.input_csv, cfg.project_key, cfg.output_json)
        elif choice == '5':
            send_json_to_xray(cfg.output_json, cfg.token, cfg.endpoint_url)
        elif choice == '6':
            print('Saliendo...')
            wait_for(1)
            clean_screen()
            break
        else:
            print('Opción inválida. Intente de nuevo.')
