"""Client for interacting with the Xray API."""
from __future__ import annotations
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


class XrayClient:
    """Simple client to send test specifications to Xray."""

    def __init__(
        self,
        token: str | None = None,
        endpoint_url: str | None = None,
        *,
        max_workers: int = 5,
    ):
        self.token = token or self._obtain_token()
        self.endpoint_url = endpoint_url or os.getenv(
            'XRAY_IMPORT_URL',
            'https://xray.cloud.getxray.app/api/v1/import/test/bulk',
        )
        # Maintain a base session for sequential uploads. Individual threads
        # will create their own sessions to avoid sharing a single instance
        # across threads (``requests.Session`` is not thread-safe).
        self._session = requests.Session()
        self._max_workers = max_workers

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

    def send_json(self, json_path: str, *, session: requests.Session | None = None):
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
        sess = session or self._session
        resp = sess.post(
            self.endpoint_url,
            headers=headers,
            data=json_body,
        )
        resp.raise_for_status()
        return resp

    def send_multiple(self, json_files: list[str]):
        """Send multiple JSON files using a thread pool."""
        successes: list[str] = []
        failures: list[tuple[str, str]] = []

        def _send(path: str) -> str:
            # Create a dedicated session per thread to avoid sharing the base
            # session between threads. ``requests.Session`` instances are not
            # guaranteed to be thread-safe and may cause issues when re-used
            # concurrently.
            with requests.Session() as sess:
                self.send_json(path, session=sess)
            return path

        with ThreadPoolExecutor(max_workers=self._max_workers) as exe:
            future_to_file = {exe.submit(_send, f): f for f in json_files}
            for fut in as_completed(future_to_file):
                fpath = future_to_file[fut]
                try:
                    fut.result()
                    successes.append(fpath)
                except Exception as exc:  # pragma: no cover - runtime errors only
                    failures.append((fpath, str(exc)))

        return successes, failures

    def close(self) -> None:
        """Close underlying HTTP session."""
        self._session.close()
