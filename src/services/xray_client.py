"""Client for interacting with the Xray API."""
from __future__ import annotations
import json
import os
import time
from datetime import datetime, timezone
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
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            # Include server response body to help diagnose failures.
            detail = ""
            try:
                data = resp.json()
                if isinstance(data, dict):
                    detail = data.get("error") or data.get("message") or str(data)
                else:
                    detail = str(data)
            except ValueError:
                detail = resp.text.strip()
            raise requests.HTTPError(f"{exc}: {detail}", response=resp) from None
        return resp

    def send_multiple(
        self,
        json_files: list[str],
        *,
        retries: int = 3,
        delay: float = 5.0,
        backoff: float = 2.0,
    ):
        """Send multiple JSON files sequentially with retry logic."""
        successes: list[str] = []
        failures: list[tuple[str, str]] = []

        for path in json_files:
            attempt = 0
            wait_time = 0.0
            while True:
                if wait_time > 0:
                    time.sleep(wait_time)
                try:
                    self.send_json(path)
                    successes.append(path)
                    break
                except requests.HTTPError as exc:
                    status = exc.response.status_code if exc.response else None
                    message = str(exc)
                    if (
                        attempt < retries
                        and status in (400, 429)
                        and (
                            "A job to import tests is already in progress" in message
                            or status == 429
                        )
                    ):
                        wait_time = delay
                        if status == 429:
                            try:
                                data = exc.response.json()
                                next_dt = data.get("nextValidRequestDate")
                                if next_dt:
                                    dt = datetime.fromisoformat(next_dt.replace("Z", "+00:00"))
                                    wait_time = max(
                                        (dt - datetime.now(timezone.utc)).total_seconds(),
                                        wait_time,
                                    )
                            except Exception:
                                pass
                        attempt += 1
                        delay *= backoff
                        continue
                    failures.append((path, message))
                    break
                except Exception as exc:  # pragma: no cover - runtime errors only
                    failures.append((path, str(exc)))
                    break

            # small cooldown between files
            time.sleep(1)

        return successes, failures

    def close(self) -> None:
        """Close underlying HTTP session."""
        self._session.close()
