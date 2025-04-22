import os
import re
import json
import time
import pandas as pd
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# -----------------------------------
# Decoradores
# -----------------------------------
def decorator_line():
    print('   ------------------------------------------------   ')

def wait_for(seconds):
    #Esperar segundos
    time.sleep(seconds)

def clean_screen():
    # Limpiar la consola
    os.system('cls' if os.name == 'nt' else 'clear')

# -----------------------------------
# Verificar archivo existente
# -----------------------------------
def verify_existing_file(path_file):
    if not os.path.isfile(path_file):
        decorator_line()
        print(f"Archivo '{path_file}' no encontrado. Intente de nuevo.")
        decorator_line()
        wait_for(2)
        clean_screen()
        return False
    return True
    

# -----------------------------------
# Solicitar un nombre de archivo
# -----------------------------------
def request_name(path_env):
    while True:
        file_name = input("Nombre del archivo (sin extensión .csv): ").strip()
        input_file = os.path.join(path_env, f"{file_name}.csv")
        if verify_existing_file(input_file):
            break
    return input_file

# -----------------------------------
# Fase 0: Autenticación
# -----------------------------------
def get_token():
    """
    Obtiene el token de API mediante client_id y client_secret definidos en el archivo .env.
    Espera encontrar en .env:
      CLIENT_ID=...
      CLIENT_SECRET=...
      AUTH_URL=https://... (URL del endpoint de autenticación)
    """
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    auth_url = os.getenv('AUTH_URL')
    if not all([client_id, client_secret, auth_url]):
        raise EnvironmentError("Faltan CLIENT_ID, CLIENT_SECRET o AUTH_URL en .env")

    payload = {
        'client_id': client_id,
        'client_secret': client_secret
    }
    headers = {'Content-Type': 'application/json'}
    resp = requests.post(auth_url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data

# -----------------------------------
# Fase 1: Configuración y carga
# -----------------------------------

def get_configuration():
    """
    Pide al usuario la configuración básica:
      - Ruta del CSV de entrada
      - Clave de proyecto por defecto
      - Define la URL del endpoint de importación
    Obtiene el token llamando a get_token().
    Calcula la ruta de salida JSON basada en el nombre del CSV.
    """
    path_env = os.getenv('PATH_FILES')

    input_csv = request_name(path_env)

    project_key = input("Clave de proyecto por defecto: ").strip()

    # Endpoints
    endpoint_url = os.getenv('XRAY_IMPORT_URL', 'https://xray.cloud.getxray.app/api/v1/import/test/bulk')
    token = get_token()

    output_json = f"{os.path.splitext(input_csv)[0]}_json.json"

    return {
        'input_csv': input_csv,
        'project_key': project_key,
        'token': token,
        'endpoint_url': endpoint_url,
        'output_json': output_json
    }

# -----------------------------------
# Fase 2: Generación de JSON
# -----------------------------------

def generate_tests_json(input_csv: str, project_key: str, output_json: str):
    """
    Lee el CSV, agrupa por Test ID (creándolo si no exista),
    construye la estructura de pruebas y escribe el JSON en disco.
    Devuelve la lista de tests generados.
    """
    df = pd.read_csv(input_csv, dtype=str, encoding='utf-8', sep=';').fillna('')

    # Asegurar Test ID
    if 'Test ID' not in df.columns:
        df['Test ID'] = df.groupby('Summary').ngroup()

    tests = []
    for test_id, group in df.groupby('Test ID', sort=False):
        first = group.iloc[0]
        test = {
            'testtype': first.get('Test Type', 'Manual'),
            'fields': {
                'project': {'key': first.get('Project Key', project_key)},
                'summary': first['Summary'],
                'description': first.get('Description', '')
            },
            'steps': []
        }

        # Carpeta y sets opcionales
        folder = first.get('Repository Folder', '')
        if folder:
            test['xray_test_repository_folder'] = folder
        sets = first.get('Test Sets', '')
        if sets:
            test['xray_test_sets'] = [s.strip() for s in re.split(r"[,;]", sets) if s.strip()]

        # Construcción de pasos
        for _, row in group.iterrows():
            action = row.get('Step', '')
            if not action:
                continue
            step = {
                'action': action,
                'data': row.get('Data', ''),
                'result': row.get('Expected Result', '')
            }
            test['steps'].append(step)

        tests.append(test)

    # Escritura de JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(tests, f, ensure_ascii=False, indent=2)

    print(f"Generados {len(tests)} tests en '{output_json}'.")
    return tests

# -----------------------------------
# Fase 3: Envío a Xray
# -----------------------------------

def send_json_to_xray(output_json: str, token: str, endpoint_url: str):
    """
    Lee el archivo JSON generado y envía una petición POST al endpoint de Xray.
    Imprime el resultado de la operación.
    """
    if verify_existing_file(output_json):
        
        with open(output_json, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response = requests.post(endpoint_url, headers=headers, json=json_data)
        if response.status_code == 200:
            print("JSON enviado exitosamente.")
        else:
            print(f"Error al enviar JSON: {response.status_code} - {response.text}")

# -----------------------------------
# Menú interactivo
# -----------------------------------

def main():
    clean_screen()
    config = get_configuration()

    while True:
        print("\n--- Menú Xray CSV->JSON -> API ---")
        print(f"1. Cambiar CSV de entrada (actual: {config['input_csv']})")
        print(f"2. Cambiar project key (actual: {config['project_key']})")
        print("3. Regenerar token de autenticación")
        print("4. Generar JSON")
        print("5. Enviar JSON a Xray")
        print("6. Salir")
        choice = input("Seleccione una opción: ").strip()

        if choice == '1':
            config['input_csv'] = input("Nuevo path del CSV de entrada: ").strip()
            config['output_json'] = f"{os.path.splitext(config['input_csv'])[0]}_json.json"
        elif choice == '2':
            config['project_key'] = input("Nueva project key: ").strip()
        elif choice == '3':
            config['token'] = get_token()
            print("Token actualizado.")
        elif choice == '4':
            generate_tests_json(
                config['input_csv'],
                config['project_key'],
                config['output_json']
            )
        elif choice == '5':
            send_json_to_xray(
                config['output_json'],
                config['token'],
                config['endpoint_url']
            )
        elif choice == '6':
            print("Saliendo...")
            wait_for(1)
            clean_screen()
            break
        else:
            print("Opción inválida. Intente de nuevo.")

if __name__ == '__main__':
    main()
