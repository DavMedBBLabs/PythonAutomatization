import os

from . import config
from .utils import (
    clean_screen,
    wait_for,
    request_file_name,
    request_json_file,
    request_excel_file,
    confirm_action,
)
from .services import (
    generate_tests_json,
    generate_jsons_from_csvs,
    excels_to_csvs,
    excel_to_csv,
    XrayClient,
    clean_json_file,
    clean_json_directory,
)


def get_configuration() -> config.Config:
    """Return initial configuration without requesting a CSV file."""
    project_key = input('Clave de proyecto por defecto [DUDBQ]: ').strip() or 'DUDBQ'
    endpoint_url = os.getenv(
        'XRAY_IMPORT_URL',
        'https://xray.cloud.getxray.app/api/v1/import/test/bulk',
    )
    token = XrayClient._obtain_token()
    # Start without a selected CSV. It can be provided later via the menu.
    return config.Config('', project_key, token, endpoint_url, '')


def interactive_menu():
    clean_screen()
    cfg = get_configuration()

    while True:
        print('\n--- Menú Xray CSV->JSON -> API ---')
        print(f"1. Cambiar project key (actual: {cfg.project_key})")
        print('2. Regenerar token de autenticación')
        print('3. Convertir Excel a CSV')
        print('4. Convertir Excel a CSV en lote')
        print('5. Convertir CSV a JSON')
        print('6. Convertir CSV a JSON en lote')
        print('7. Enviar JSON a Xray')
        print('8. Enviar JSON a Xray en lote')
        print('9. Limpiar JSONs')
        print('0. Salir')
        choice = input('Seleccione una opción: ').strip()

        if choice == '1':
            cfg.project_key = input('Nueva project key: ').strip() or cfg.project_key
        elif choice == '2':
            cfg.token = XrayClient._obtain_token()
            print('Token actualizado.')
        elif choice == '3':
            excel_path = request_excel_file(config.excel_path())
            base = os.path.splitext(os.path.basename(excel_path))[0]
            csv_path = os.path.join(config.env_path(), f"{base}.csv")
            excel_to_csv(excel_path, csv_path)
        elif choice == '4':
            excel_dir = config.excel_path()
            csv_dir = config.env_path()
            successes, failures = excels_to_csvs(excel_dir, csv_dir)
            print(f'Conversión completada. Éxitos: {len(successes)} - Fallos: {len(failures)}')
            for fpath, reason in failures:
                print(f"Falló {os.path.basename(fpath)}: {reason}")
        elif choice == '5':
            csv_name = request_file_name(config.env_path())
            csv_path = os.path.join(config.env_path(), csv_name)
            json_out = os.path.join(config.json_path(), f"{os.path.splitext(csv_name)[0]}.json")
            generate_tests_json(csv_path, cfg.project_key, json_out)
        elif choice == '6':
            csv_dir = config.env_path()
            json_dir = config.json_path()
            successes, failures = generate_jsons_from_csvs(csv_dir, cfg.project_key, json_dir)
            print(f'Conversión completada. Éxitos: {len(successes)} - Fallos: {len(failures)}')
            for fpath, reason in failures:
                print(f"Falló {os.path.basename(fpath)}: {reason}")
        elif choice == '7':
            json_path = request_json_file(config.json_path())
            if confirm_action(f"Enviar '{os.path.basename(json_path)}' a Xray?"):
                client = XrayClient(cfg.token, cfg.endpoint_url)
                try:
                    client.send_json(json_path)
                    print('JSON enviado exitosamente.')
                except Exception as exc:
                    print(f'Error al enviar JSON: {exc}')
        elif choice == '8':
            send_opt = input('1. Enviar por lista de números\n2. Enviar todo\nSeleccione una opción: ').strip()
            json_dir = config.json_path()
            all_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
            if send_opt == '1':
                nums = input('Números separados por coma: ').split(',')
                nums = [n.strip() for n in nums if n.strip()]
                files = [os.path.join(json_dir, f) for f in all_files if any(f.startswith(num) for num in nums)]
            else:
                files = [os.path.join(json_dir, f) for f in all_files]
            if not files:
                print('No se encontraron archivos para enviar.')
            elif confirm_action(f"Enviar {len(files)} archivos a Xray?"):
                client = XrayClient(cfg.token, cfg.endpoint_url)
                successes, failures = client.send_multiple(files)
                print(f'Envío completado. Éxitos: {len(successes)} - Fallos: {len(failures)}')
                for fpath, reason in failures:
                    print(f"Falló {os.path.basename(fpath)}: {reason}")
        elif choice == '9':
            clean_opt = input('1. Limpiar un archivo\n2. Limpiar todo\nSeleccione una opción: ').strip()
            json_dir = config.json_path()
            if clean_opt == '1':
                json_file = request_json_file(json_dir)
                clean_json_file(json_file)
                print(f"Archivo '{os.path.basename(json_file)}' limpiado.")
            else:
                cleaned = clean_json_directory(json_dir)
                print(f'{len(cleaned)} archivos limpiados.')
        elif choice == '0':
            print('Saliendo...')
            wait_for(1)
            clean_screen()
            break
        else:
            print('Opción inválida. Intente de nuevo.')
