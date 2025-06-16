"""Read Excel test specs and send them to Xray."""
from __future__ import annotations

from pathlib import Path
import re
from typing import List, Tuple

import pandas as pd

from .cleanup import clean_json_data
from .xray_client import XrayClient


_COLUMNS = [
    "Test ID",
    "Summary",
    "Description",
    "Step",
    "Data",
    "Expected Result",
]


def _read_excel(path: str) -> pd.DataFrame:
    """Return DataFrame from Excel *path* assuming no headers."""
    df = pd.read_excel(path, header=None, dtype=str).fillna("")
    df = df.iloc[:, : len(_COLUMNS)]
    df.columns = _COLUMNS[: df.shape[1]]
    return df


def _split_tests(df: pd.DataFrame) -> list[pd.DataFrame]:
    """Split DataFrame into tests whenever "Test ID" restarts at 1."""
    groups: list[pd.DataFrame] = []
    start = 0
    for idx in range(1, len(df)):
        if str(df.at[idx, "Test ID"]).strip() == "1":
            groups.append(df.iloc[start:idx])
            start = idx
    groups.append(df.iloc[start:])
    return groups


def tests_from_excel(excel_path: str, project_key: str) -> list[dict]:
    """Parse *excel_path* and return a list of test payloads."""
    df = _read_excel(excel_path)
    folders = [f"HU-{num}" for num in re.findall(r"\d+", Path(excel_path).stem)]
    groups = _split_tests(df)

    tests: list[dict] = []
    for i, group in enumerate(groups):
        first = group.iloc[0]
        folder = folders[i] if i < len(folders) else ""
        test = {
            "testtype": "Manual",
            "xray_test_repository_folder": folder,
            "fields": {
                "project": {"key": project_key},
                "summary": first.get("Summary", ""),
                "description": first.get("Description", ""),
            },
            "steps": [],
        }
        for _, row in group.iterrows():
            test["steps"].append(
                {
                    "action": row.get("Step", ""),
                    "data": row.get("Data", ""),
                    "result": row.get("Expected Result", ""),
                }
            )
        tests.append(test)

    clean_json_data(tests)
    return tests


def send_excel_to_xray(
    excel_path: str, project_key: str, client: XrayClient
) -> Tuple[List[int], List[Tuple[int, str]]]:
    """Send tests defined in *excel_path* to Xray using *client*."""
    tests = tests_from_excel(excel_path, project_key)
    successes: list[int] = []
    failures: list[Tuple[int, str]] = []

    for idx, test in enumerate(tests, start=1):
        try:
            client.send_tests([test])
            successes.append(idx)
        except Exception as exc:  # pragma: no cover - runtime errors only
            failures.append((idx, str(exc)))

    return successes, failures
