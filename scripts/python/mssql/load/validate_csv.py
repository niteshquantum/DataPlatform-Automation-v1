import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]

from scripts.python.common.column_mapper import (
    load_mapping_config,
    resolve_source_file_stem,
    get_source_to_target_mapping,
)


def main():
    with (ROOT / 'metadata' / 'mssql' / 'schema_registry.json').open(encoding='utf-8') as source:
        registry = json.load(source)

    mapping_config = load_mapping_config()

    for table, columns in registry.items():
        source_stem = resolve_source_file_stem(table, mapping_config, "mssql")
        path = ROOT / 'incoming' / 'mssql' / f'{source_stem}.csv'
        if not path.exists():
            raise FileNotFoundError(f'Required file missing: {path.name}')
        frame = pd.read_csv(path, encoding='utf-8-sig')
        if frame.empty:
            raise ValueError(f'CSV file is empty: {path.name}')

        source_headers = list(frame.columns)
        source_to_target = get_source_to_target_mapping(source_headers, mapping_config)
        target_to_source = {v: k for k, v in source_to_target.items()}

        missing = []
        for target_col in columns:
            source_col = target_to_source.get(target_col)
            if source_col is None or source_col not in source_headers:
                missing.append(target_col)

        if missing:
            raise ValueError(f'Invalid CSV {path.name}; missing columns: {missing}')
        print(f'[OK] {path.name} ({len(frame)} rows)')


if __name__ == '__main__':
    main()
