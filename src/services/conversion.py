"""Utilities for converting between file formats."""
from __future__ import annotations
import json
import os
from pathlib import Path
import pandas as pd
import re

from .cleanup import clean_json_data


def generate_tests_json(
    input_csv: str, project_key: str, output_json: str, sep: str = ','
) -> list[dict]:
    """Convert a CSV test specification to an Xray-compatible JSON file."""
    csv_path = Path(input_csv)
    out_path = Path(output_json)
    try:
        df = pd.read_csv(
            csv_path,
            dtype=str,
            encoding='utf-8',
            sep=sep,
            skipinitialspace=True,
        ).fillna('')
    except Exception as exc:  # pragma: no cover - runtime errors only
        raise ValueError(f'No se pudo leer CSV {input_csv}: {exc}')
    df = df.dropna(how='all')
    df.columns = df.columns.str.strip()

    required = {'Summary', 'Step'}
    if not required.issubset(df.columns):
        raise ValueError(
            'El CSV no contiene las columnas requeridas o el separador es incorrecto'
        )

    if 'Test ID' not in df.columns:
        df['Test ID'] = df.groupby('Summary').ngroup()

    tests = []
    for _, group in df.groupby('Test ID', sort=False):
        first = group.iloc[0]
        test = {
            'testtype': (first.get('Test Type', 'Manual') or 'Manual').strip(),
            'fields': {
                'project': {'key': first.get('Project Key', project_key)},
                'summary': first['Summary'],
                'description': first.get('Description', ''),
            },
            'steps': [],
        }

        folder = first.get('Repository Folder', '')
        if folder:
            test['xray_test_repository_folder'] = folder.strip()
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

    clean_json_data(tests)

    with out_path.open('w', encoding='utf-8') as f:
        json.dump(tests, f, ensure_ascii=False, indent=2)

    print(f"Generados {len(tests)} tests en '{out_path}'.")
    return tests


def generate_jsons_from_csvs(
    csv_dir: str, project_key: str, json_dir: str, sep: str = ','
) -> tuple[list[str], list[tuple[str, str]]]:
    """Convert all CSV files in *csv_dir* to JSON format in *json_dir*."""
    successes: list[str] = []
    failures: list[tuple[str, str]] = []
    csv_path = Path(csv_dir)
    json_path = Path(json_dir)
    for csv_file in csv_path.glob('*.csv'):
        out_file = json_path / f"{csv_file.stem}.json"
        try:
            generate_tests_json(str(csv_file), project_key, str(out_file), sep)
            successes.append(str(csv_file))
        except Exception as exc:  # pragma: no cover - runtime errors only
            failures.append((str(csv_file), str(exc)))
    return successes, failures


def excels_to_csvs(excel_dir: str, csv_dir: str):
    """Convert Excel files in *excel_dir* to CSV format in *csv_dir*."""
    successes: list[str] = []
    failures: list[tuple[str, str]] = []
    excel_path = Path(excel_dir)
    csv_path = Path(csv_dir)
    for file in excel_path.glob('*.xlsx'):
        csv_file = csv_path / f"{file.stem}.csv"
        try:
            excel_to_csv(str(file), str(csv_file))
            successes.append(str(csv_file))
        except Exception as exc:  # pragma: no cover - runtime errors only
            failures.append((str(file), str(exc)))
    for file in excel_path.glob('*.xls'):
        csv_file = csv_path / f"{file.stem}.csv"
        try:
            excel_to_csv(str(file), str(csv_file))
            successes.append(str(csv_file))
        except Exception as exc:  # pragma: no cover - runtime errors only
            failures.append((str(file), str(exc)))
    return successes, failures


def excel_to_csv(excel_path: str, csv_path: str):
    """Convert a single Excel file to CSV."""
    src = Path(excel_path)
    dst = Path(csv_path)
    try:
        df = pd.read_excel(src, dtype=str).fillna('')
        df.to_csv(dst, index=False, encoding='utf-8')
    except Exception as exc:  # pragma: no cover - runtime errors only
        raise ValueError(f'Error al convertir {src}: {exc}')
    print(f"Generado '{dst}' desde '{src}'.")
    return str(dst)
