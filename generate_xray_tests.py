import pandas as pd
import json
import re

# Configuration
INPUT_CSV = 'tests3.csv'         # CSV file path
OUTPUT_JSON = 'tests3.json'      # Output JSON file path
PROJECT_KEY = 'RTBQ'            # Default project key if not in CSV

# Read CSV
df = pd.read_csv(INPUT_CSV, dtype=str, encoding='utf-8', sep=';').fillna('')

# Ensure Test ID exists (if not, create one per unique Summary)
if 'Test ID' not in df.columns:
    df['Test ID'] = df.groupby('Summary').ngroup()

# Group rows by Test ID
tests = []
for test_id, group in df.groupby('Test ID', sort=False):
    first = group.iloc[0]
    # Build base test structure
    test = {
        "testtype": first.get('Test Type', 'Manual'),
        "fields": {
            "project": { "key": first.get('Project Key', PROJECT_KEY) },
            "summary": first['Summary'],
            "description": first.get('Description', '')
        },
        "steps": [],
    }
    # Optional: folder and test sets columns
    folder = first.get('Repository Folder', '')
    if folder:
        test["xray_test_repository_folder"] = folder
    sets = first.get('Test Sets', '')
    if sets:
        # Support comma- or semicolon-separated lists
        test["xray_test_sets"] = [s.strip() for s in re.split(r'[,;]', sets) if s.strip()]
    
    # Build steps
    for _, row in group.iterrows():
        action = row.get('Step', '')
        if not action:
            continue
        step = {
            "action": action,
            "data": row.get('Data', ''),
            "result": row.get('Expected Result', '')
        }
        test["steps"].append(step)
    
    tests.append(test)

# Write JSON file
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(tests, f, ensure_ascii=False, indent=2)

print(f"Generated {len(tests)} test(s) in '{OUTPUT_JSON}'.")
