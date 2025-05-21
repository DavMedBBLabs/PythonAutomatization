import json
import os
import pandas as pd
import re


def generate_tests_json(input_csv: str, project_key: str, output_json: str):
    df = pd.read_csv(input_csv, dtype=str, encoding='utf-8', sep=';').fillna('')

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
                'description': first.get('Description', '')
            },
            'steps': []
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
                'result': row.get('Expected Result', '')
            }
            test['steps'].append(step)

        tests.append(test)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(tests, f, ensure_ascii=False, indent=2)

    print(f"Generados {len(tests)} tests en '{output_json}'.")
    return tests
