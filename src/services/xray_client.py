"""Client for interacting with the Xray API."""
from __future__ import annotations
import json
import os
import requests


class XrayClient:
    """Simple client to send test specifications to Xray."""

    def __init__(self, token: str | None = None, endpoint_url: str | None = None):
        self.token = token or self._obtain_token()
        self.endpoint_url = endpoint_url or os.getenv(
            'XRAY_IMPORT_URL',
            'https://xray.cloud.getxray.app/api/v1/import/test/bulk',
        )

    @staticmethod
    def _obtain_token() -> str:
        """Return an auth token, accepting JSON or plain text responses."""
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET')
        auth_url = os.getenv('AUTH_URL')
        if not all([client_id, client_secret, auth_url]):
            raise EnvironmentError('Faltan CLIENT_ID, CLIENT_SECRET o AUTH_URL en .env')

        payload = {'client_id': client_id, 'client_secret': client_secret}
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(auth_url, headers=headers, json=payload)
        resp.raise_for_status()
        try:
            data = resp.json()
            token = data['token'] if isinstance(data, dict) else data
        except ValueError:
            token = resp.text
        return token.strip()

    def send_json(self, json_path: str):
        """Send a JSON file to Xray."""
        if not os.path.isfile(json_path):
            raise FileNotFoundError(json_path)
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        json_body = json.dumps(json_data, ensure_ascii=False).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}',
        }
        resp = requests.post(
            self.endpoint_url,
            headers=headers,
            data=json_body,
        )
        resp.raise_for_status()
        return resp

    def send_multiple(self, json_files: list[str]):
        """Send multiple JSON files sequentially."""
        successes: list[str] = []
        failures: list[tuple[str, str]] = []
        for json_file in json_files:
            try:
                self.send_json(json_file)
                successes.append(json_file)
            except Exception as exc:  # pragma: no cover - runtime errors only
                failures.append((json_file, str(exc)))
        return successes, failures
