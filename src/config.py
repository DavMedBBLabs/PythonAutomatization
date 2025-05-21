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
    path = os.path.join(env_path(), 'json')
    os.makedirs(path, exist_ok=True)
    return path
