import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]


def main():
    with (ROOT / 'metadata' / 'mssql' / 'schema_registry.json').open(encoding='utf-8') as source:
        registry = json.load(source)
    for table, columns in registry.items():
        path = ROOT / 'incoming' / 'mssql' / f'{table}.csv'
        if not path.exists():
            raise FileNotFoundError(f'Required file missing: {path.name}')
        frame = pd.read_csv(path, encoding='utf-8-sig')
        missing = [column for column in columns if column not in frame.columns]
        if frame.empty or missing:
            raise ValueError(f'Invalid CSV {path.name}; missing columns: {missing}')
        print(f'[OK] {path.name} ({len(frame)} rows)')


if __name__ == '__main__':
    main()
