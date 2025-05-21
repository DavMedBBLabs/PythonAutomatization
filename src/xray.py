"""Backwards compatibility wrappers for the Xray client."""
from .services.xray_client import XrayClient

get_token = XrayClient._obtain_token


def send_json_to_xray(output_json: str, token: str, endpoint_url: str) -> None:
    client = XrayClient(token, endpoint_url)
    client.send_json(output_json)


def send_jsons_to_xray(json_files: list[str], token: str, endpoint_url: str):
    client = XrayClient(token, endpoint_url)
    return client.send_multiple(json_files)
