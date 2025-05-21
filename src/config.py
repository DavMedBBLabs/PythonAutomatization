from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    input_csv: str
    project_key: str
    token: str
    endpoint_url: str
    output_json: str


def env_path() -> str:
    return os.getenv('PATH_FILES', '.')


def json_path() -> str:
    """Return path for generated JSON files ensuring it exists."""
    base = os.getenv('PATH_JSON', os.path.join(env_path(), 'json'))
    os.makedirs(base, exist_ok=True)
    return base


def excel_path() -> str:
    """Return path for Excel source files ensuring it exists."""
    base = os.getenv('PATH_EXCEL', os.path.join(env_path(), 'excel'))
    os.makedirs(base, exist_ok=True)
    return base
