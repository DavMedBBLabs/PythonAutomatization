"""Utilities for cleaning JSON test files."""
from __future__ import annotations

import glob
import json
import os
from typing import Any

__all__ = ["clean_json_data", "clean_json_file", "clean_json_directory"]


def clean_json_data(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip whitespace from known fields in test definitions."""
    for test in data:
        if "testtype" in test and isinstance(test["testtype"], str):
            test["testtype"] = test["testtype"].strip()
        if "xray_test_repository_folder" in test and isinstance(
            test["xray_test_repository_folder"], str
        ):
            test["xray_test_repository_folder"] = test["xray_test_repository_folder"].strip()
        if "fields" in test and isinstance(test["fields"], dict):
            for k in ["summary", "description"]:
                if k in test["fields"] and isinstance(test["fields"][k], str):
                    test["fields"][k] = test["fields"][k].strip()
        if "steps" in test and isinstance(test["steps"], list):
            for step in test["steps"]:
                if not isinstance(step, dict):
                    continue
                for k in ["action", "data", "result"]:
                    if k in step and isinstance(step[k], str):
                        step[k] = step[k].strip()
    return data


def clean_json_file(filepath: str) -> list[dict[str, Any]]:
    """Clean a JSON file in place and return the cleaned data."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    clean_json_data(data)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def clean_json_directory(directory: str, pattern: str = "*.json") -> list[str]:
    """Clean all JSON files matching *pattern* within *directory*."""
    cleaned: list[str] = []
    for path in glob.glob(os.path.join(directory, pattern)):
        clean_json_file(path)
        cleaned.append(path)
    return cleaned
