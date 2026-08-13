import re
from pathlib import Path

TABLE_PATTERN = re.compile(r'tableName="([^"]+)"', re.IGNORECASE)
COLUMN_PATTERN = re.compile(r'<column\s+name="([^"]+)"', re.IGNORECASE)
CHANGESET_ID_PATTERN = re.compile(r'<changeSet[^>]+id="([^"]+)"', re.IGNORECASE)
CHANGESET_AUTHOR_PATTERN = re.compile(r'<changeSet[^>]+author="([^"]+)"', re.IGNORECASE)
NUMERIC_PREFIX_PATTERN = re.compile(r'^(\d{3})_')


def parse_liquibase_file(file_path):
    """Parse a Liquibase XML file and collect metadata for generator decisions."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    table_match = TABLE_PATTERN.search(content)
    if not table_match:
        return None

    change_id_match = CHANGESET_ID_PATTERN.search(content)
    author_match = CHANGESET_AUTHOR_PATTERN.search(content)
    columns = {c.lower() for c in COLUMN_PATTERN.findall(content)}

    return {
        "path": file_path,
        "file_name": file_path.name,
        "table_name": table_match.group(1).lower(),
        "columns": columns,
        "change_id": change_id_match.group(1) if change_id_match else None,
        "author": author_match.group(1) if author_match else None,
    }


def collect_existing_change_files(liquibase_dir, exclude_names=None):
    """Collect parsed Liquibase change files under a directory."""
    exclude_names = set(exclude_names or [])
    results = []

    for file_path in sorted(liquibase_dir.glob("*.xml")):
        if file_path.name in exclude_names:
            continue
        parsed = parse_liquibase_file(file_path)
        if parsed:
            results.append(parsed)

    return results


def get_next_change_number(file_paths):
    """Return the next available three-digit change number based on existing file names."""
    max_number = 0
    for file_path in file_paths:
        match = NUMERIC_PREFIX_PATTERN.match(file_path.name)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number + 1
