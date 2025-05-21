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
