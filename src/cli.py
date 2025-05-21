import os

from . import config
from .utils import clean_screen, wait_for, request_file_name, request_json_file
from .services import (
    generate_tests_json,
    generate_jsons_from_csvs,
    excels_to_csvs,
    XrayClient,
)


def get_configuration() -> config.Config:
    input_csv = request_file_name(config.env_path())
    project_key = input('Clave de proyecto por defecto: ').strip()
    endpoint_url = os.getenv(
        'XRAY_IMPORT_URL',
        'https://xray.cloud.getxray.app/api/v1/import/test/bulk',
    )
    token = XrayClient._obtain_token()
    output_json = os.path.join(
        config.json_path(), f"{os.path.splitext(input_csv)[0]}.json")
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
        print('6. Enviar todos los JSON a Xray')
        print('7. Convertir todos los CSV a JSON')
        print('8. Convertir Excel a CSV')
        print('9. Salir')
        choice = input('Seleccione una opción: ').strip()

        if choice == '1':
            cfg.input_csv = request_file_name(config.env_path())
            cfg.output_json = os.path.join(
                config.json_path(), f"{os.path.splitext(cfg.input_csv)[0]}.json")
        elif choice == '2':
            cfg.project_key = input('Nueva project key: ').strip()
        elif choice == '3':
            cfg.token = XrayClient._obtain_token()
            print('Token actualizado.')
        elif choice == '4':
            csv_path = os.path.join(config.env_path(), cfg.input_csv)
            generate_tests_json(csv_path, cfg.project_key, cfg.output_json)
        elif choice == '5':
            json_path = request_json_file(config.json_path())
            client = XrayClient(cfg.token, cfg.endpoint_url)
            try:
                client.send_json(json_path)
                print('JSON enviado exitosamente.')
            except Exception as exc:
                print(f'Error al enviar JSON: {exc}')
        elif choice == '6':
            json_dir = config.json_path()
            files = [os.path.join(json_dir, f) for f in os.listdir(json_dir) if f.endswith('.json')]
            client = XrayClient(cfg.token, cfg.endpoint_url)
            successes, failures = client.send_multiple(files)
            print(f'Envío completado. Éxitos: {len(successes)} - Fallos: {len(failures)}')
            for fpath, reason in failures:
                print(f"Falló {os.path.basename(fpath)}: {reason}")
        elif choice == '7':
            csv_dir = config.env_path()
            json_dir = config.json_path()
            successes, failures = generate_jsons_from_csvs(csv_dir, cfg.project_key, json_dir)
            print(f'Conversión completada. Éxitos: {len(successes)} - Fallos: {len(failures)}')
            for fpath, reason in failures:
                print(f"Falló {os.path.basename(fpath)}: {reason}")
        elif choice == '8':
            excel_dir = config.excel_path()
            csv_dir = config.env_path()
            successes, failures = excels_to_csvs(excel_dir, csv_dir)
            print(f'Conversión completada. Éxitos: {len(successes)} - Fallos: {len(failures)}')
            for fpath, reason in failures:
                print(f"Falló {os.path.basename(fpath)}: {reason}")
        elif choice == '9':
            print('Saliendo...')
            wait_for(1)
            clean_screen()
            break
        else:
            print('Opción inválida. Intente de nuevo.')
