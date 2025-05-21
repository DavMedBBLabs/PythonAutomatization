import os
import json
import requests

from .utils import verify_existing_file


def get_token() -> str:
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    auth_url = os.getenv('AUTH_URL')
    if not all([client_id, client_secret, auth_url]):
        raise EnvironmentError('Faltan CLIENT_ID, CLIENT_SECRET o AUTH_URL en .env')

    payload = {'client_id': client_id, 'client_secret': client_secret}
    headers = {'Content-Type': 'application/json'}
    resp = requests.post(auth_url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()['token'] if isinstance(resp.json(), dict) else resp.text


def send_json_to_xray(output_json: str, token: str, endpoint_url: str) -> None:
    if not verify_existing_file(output_json):
        return

    with open(output_json, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    response = requests.post(endpoint_url, headers=headers, json=json_data)
    if response.status_code == 200:
        print('JSON enviado exitosamente.')
    else:
        print(f'Error al enviar JSON: {response.status_code} - {response.text}')


def send_jsons_to_xray(json_files: list[str], token: str, endpoint_url: str):
    """Send multiple JSON files sequentially and return the results.

    Args:
        json_files: List of paths to JSON files.
        token: Authentication token.
        endpoint_url: Xray endpoint URL.

    Returns:
        Tuple with a list of successfully processed files and a list of tuples
        with the file that failed and the associated error message.
    """
    successes = []
    failures = []
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    for json_file in json_files:
        if not verify_existing_file(json_file):
            failures.append((json_file, 'Archivo no encontrado'))
            continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            resp = requests.post(endpoint_url, headers=headers, json=json_data)
            if resp.status_code == 200:
                successes.append(json_file)
            else:
                failures.append((json_file, f'Status {resp.status_code} - {resp.text}'))
        except Exception as exc:  # Catch unexpected errors
            failures.append((json_file, str(exc)))

    return successes, failures
