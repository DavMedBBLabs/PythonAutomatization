"""Utilities for converting between file formats."""
from __future__ import annotations
import json
import os
import pandas as pd
import re


def generate_tests_json(input_csv: str, project_key: str, output_json: str):
    """Convert a CSV test specification to an Xray-compatible JSON file."""
    df = (
        pd.read_csv(input_csv, dtype=str, encoding='utf-8', sep=',', skipinitialspace=True)
        .fillna('')
    )
    df = df.dropna(how='all')
    df.columns = df.columns.str.strip()

    if 'Test ID' not in df.columns:
        df['Test ID'] = df.groupby('Summary').ngroup()

    tests = []
    for _, group in df.groupby('Test ID', sort=False):
        first = group.iloc[0]
        test = {
            'testtype': first.get('Test Type', 'Manual'),
            'fields': {
                'project': {'key': first.get('Project Key', project_key)},
                'summary': first['Summary'],
                'description': first.get('Description', ''),
            },
            'steps': [],
        }

        folder = first.get('Repository Folder', '')
        if folder:
            test['xray_test_repository_folder'] = folder
        sets = first.get('Test Sets', '')
        if sets:
            test['xray_test_sets'] = [s.strip() for s in re.split(r'[;,]', sets) if s.strip()]

        for _, row in group.iterrows():
            action = row.get('Step', '')
            if not action:
                continue
            step = {
                'action': action,
                'data': row.get('Data', ''),
                'result': row.get('Expected Result', ''),
            }
            test['steps'].append(step)

        tests.append(test)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(tests, f, ensure_ascii=False, indent=2)

    print(f"Generados {len(tests)} tests en '{output_json}'.")
    return tests


def generate_jsons_from_csvs(csv_dir: str, project_key: str, json_dir: str):
    """Convert all CSV files in *csv_dir* to JSON format in *json_dir*."""
    successes: list[str] = []
    failures: list[tuple[str, str]] = []
    for name in os.listdir(csv_dir):
        if not name.lower().endswith('.csv'):
            continue
        csv_path = os.path.join(csv_dir, name)
        json_name = f"{os.path.splitext(name)[0]}.json"
        json_path = os.path.join(json_dir, json_name)
        try:
            generate_tests_json(csv_path, project_key, json_path)
            successes.append(csv_path)
        except Exception as exc:  # pragma: no cover - runtime errors only
            failures.append((csv_path, str(exc)))
    return successes, failures


def excels_to_csvs(excel_dir: str, csv_dir: str):
    """Convert Excel files in *excel_dir* to CSV format in *csv_dir*."""
    successes: list[str] = []
    failures: list[tuple[str, str]] = []
    for name in os.listdir(excel_dir):
        if not name.lower().endswith(('.xlsx', '.xls')):
            continue
        excel_path = os.path.join(excel_dir, name)
        csv_name = f"{os.path.splitext(name)[0]}.csv"
        csv_path = os.path.join(csv_dir, csv_name)
        try:
            df = pd.read_excel(excel_path, dtype=str).fillna('')
            df.to_csv(csv_path, index=False, encoding='utf-8')
            successes.append(csv_path)
        except Exception as exc:  # pragma: no cover - runtime errors only
            failures.append((excel_path, str(exc)))
    return successes, failures


def excel_to_csv(excel_path: str, csv_path: str):
    """Convert a single Excel file to CSV."""
    df = pd.read_excel(excel_path, dtype=str).fillna('')
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Generado '{csv_path}' desde '{excel_path}'.")
    return csv_path
