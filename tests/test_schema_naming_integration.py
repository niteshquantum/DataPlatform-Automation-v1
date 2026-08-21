#!/usr/bin/env python

"""
Integration tests for schema_detector + naming_engine flow.

Tests the actual CSV -> schema_registry.json + table_source_mapping.json
pipeline with naming engine enabled and disabled.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest

from scripts.python.common.column_mapper import (
    load_mapping_config,
    load_naming_config,
    map_table_name,
    map_columns,
    get_source_to_target_mapping,
)
from scripts.schema_detector import (
    get_csv_headers,
    update_schema_registry,
    update_table_source_mapping,
    detect_schema_changes,
)


# ============================================================
# HELPERS
# ============================================================

def write_csv(path, headers, rows):
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def run_schema_detection(tmp_path, db_type="mysql", enable_naming_engine=False):
    # Setup config overrides via monkeypatch
    import scripts.python.common.column_mapper as cm
    import scripts.schema_detector as sd

    old_naming_config = cm.load_naming_config()
    old_mapping_config = cm.load_mapping_config()

    naming_config = dict(old_naming_config)
    naming_config["settings"] = {"enable_naming_engine": enable_naming_engine}
    cm.NAMING_CONFIG_PATH = tmp_path / "naming_rules.json"
    with open(cm.NAMING_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(naming_config, f)

    mapping_config = dict(old_mapping_config)
    mapping_config["settings"] = {"enable_mapping": True}
    cm.CONFIG_PATH = tmp_path / "column_mapping.json"
    with open(cm.CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping_config, f)

    # Override schema_detector paths
    incoming_dir = tmp_path / "incoming" / db_type
    incoming_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir = tmp_path / "metadata" / db_type
    metadata_dir.mkdir(parents=True, exist_ok=True)

    sd.ROOT = tmp_path

    registry_path = metadata_dir / "schema_registry.json"
    table_source_mapping_path = metadata_dir / "table_source_mapping.json"

    # Run detection logic inline (avoid running main() which parses argv)
    results = []
    for csv_file in incoming_dir.glob("*.csv"):
        source_table_name = csv_file.stem.strip()
        target_table_name = cm.resolve_table_mapping(source_table_name, mapping_config)
        headers = get_csv_headers(csv_file)
        if headers:
            target_headers = cm.map_columns(headers, mapping_config, source_table_name)
            existing_columns = []
            if registry_path.exists():
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)
                existing_columns = registry.get(target_table_name, [])
            result = detect_schema_changes(existing_columns, target_headers)
            update_schema_registry(target_table_name, target_headers, registry_path)
            update_table_source_mapping(target_table_name, source_table_name, table_source_mapping_path)
            results.append({
                "source_table": source_table_name,
                "target_table": target_table_name,
                "source_headers": headers,
                "target_headers": target_headers,
                "status": result["status"],
            })

    # Read final registry
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)
    with open(table_source_mapping_path, "r", encoding="utf-8") as f:
        table_source_mapping = json.load(f)

    return registry, table_source_mapping, results


# ============================================================
# TEST A — naming disabled (backward compatibility)
# ============================================================

def test_naming_disabled_preserves_existing_behavior(tmp_path):
    incoming = tmp_path / "incoming" / "mysql"
    incoming.mkdir(parents=True, exist_ok=True)
    write_csv(
        incoming / "employees.csv",
        ["emp_id", "first_name", "last_name"],
        [["1", "John", "Doe"]],
    )

    registry, table_source_mapping, results = run_schema_detection(
        tmp_path, enable_naming_engine=False
    )

    assert "employees" in registry
    assert registry["employees"] == ["emp_id", "first_name", "last_name"]
    assert table_source_mapping["employees"] == "employees"
    assert results[0]["status"] == "NEW"


# ============================================================
# TEST B — table override
# ============================================================

def test_table_override(tmp_path):
    incoming = tmp_path / "incoming" / "mysql"
    incoming.mkdir(parents=True, exist_ok=True)
    write_csv(
        incoming / "Customer Records.csv",
        ["CustomerID", "FirstName", "LastName"],
        [["1", "John", "Doe"]],
    )

    naming_rules = {
        "version": "1.0",
        "settings": {"enable_naming_engine": True},
        "table": {
            "style": "snake_case",
            "character_replacements": {" ": "_", "-": "_", ".": "_"},
            "overrides": {"Customer Records": "customers"},
        },
        "column": {
            "style": "snake_case",
            "character_replacements": {" ": "_", "-": "_", ".": "_"},
            "overrides": {},
        },
        "collision": {"strategy": "suffix", "separator": "_", "start_index": 2},
    }
    naming_path = tmp_path / "naming_rules.json"
    with open(naming_path, "w", encoding="utf-8") as f:
        json.dump(naming_rules, f)

    import scripts.python.common.column_mapper as cm
    cm.NAMING_CONFIG_PATH = naming_path

    registry, table_source_mapping, results = run_schema_detection(
        tmp_path, enable_naming_engine=True
    )

    assert "customers" in registry
    assert registry["customers"] == ["customer_id", "first_name", "last_name"]
    assert table_source_mapping["customers"] == "Customer Records"


# ============================================================
# TEST C — generic naming
# ============================================================

def test_generic_naming_snake_case(tmp_path):
    incoming = tmp_path / "incoming" / "mysql"
    incoming.mkdir(parents=True, exist_ok=True)
    write_csv(
        incoming / "Sales-Data.csv",
        ["Order ID", "Customer-ID", "Order.Amount"],
        [["1", "C1", "99.99"]],
    )

    naming_rules = {
        "version": "1.0",
        "settings": {"enable_naming_engine": True},
        "table": {
            "style": "snake_case",
            "character_replacements": {" ": "_", "-": "_", ".": "_"},
            "overrides": {},
        },
        "column": {
            "style": "snake_case",
            "character_replacements": {" ": "_", "-": "_", ".": "_"},
            "overrides": {},
        },
        "collision": {"strategy": "suffix", "separator": "_", "start_index": 2},
    }
    naming_path = tmp_path / "naming_rules.json"
    with open(naming_path, "w", encoding="utf-8") as f:
        json.dump(naming_rules, f)

    import scripts.python.common.column_mapper as cm
    cm.NAMING_CONFIG_PATH = naming_path

    registry, table_source_mapping, results = run_schema_detection(
        tmp_path, enable_naming_engine=True
    )

    assert "sales_data" in registry
    assert registry["sales_data"] == ["order_id", "customer_id", "order_amount"]
    assert table_source_mapping["sales_data"] == "Sales-Data"


# ============================================================
# TEST D-I — naming styles
# ============================================================

def test_naming_styles_via_column_mapper():
    import scripts.python.common.column_mapper as cm

    test_cases = [
        ("snake_case", "Customer ID", "customer_id"),
        ("camelCase", "Customer ID", "customerId"),
        ("PascalCase", "Customer ID", "CustomerId"),
        ("kebab-case", "Customer ID", "customer-id"),
        ("lowercase", "Customer ID", "customer id"),
        ("UPPERCASE", "Customer ID", "CUSTOMER ID"),
        ("preserve", "Customer ID", "Customer ID"),
    ]

    for style, input_name, expected in test_cases:
        naming_rules = {
            "version": "1.0",
            "settings": {"enable_naming_engine": True},
            "table": {"style": style, "character_replacements": {}, "overrides": {}},
            "column": {"style": style, "character_replacements": {}, "overrides": {}},
            "collision": {"strategy": "suffix", "separator": "_", "start_index": 2},
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(naming_rules, f)
            naming_path = Path(f.name)

        cm.NAMING_CONFIG_PATH = naming_path
        result = cm.map_columns([input_name], {})
        assert result == [expected], f"Style {style}: expected {expected}, got {result}"
        naming_path.unlink(missing_ok=True)


# ============================================================
# TEST J — dynamic replacement
# ============================================================

def test_dynamic_replacement_no_code_change():
    import scripts.python.common.column_mapper as cm
    import tempfile

    naming_rules = {
        "version": "1.0",
        "settings": {"enable_naming_engine": True},
        "table": {
            "style": "snake_case",
            "character_replacements": {" ": "_", "-": "_", ".": "_", "$": "_"},
            "overrides": {},
        },
        "column": {
            "style": "snake_case",
            "character_replacements": {" ": "_", "-": "_", ".": "_", "$": "_"},
            "overrides": {},
        },
        "collision": {"strategy": "suffix", "separator": "_", "start_index": 2},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(naming_rules, f)
        naming_path = Path(f.name)

    cm.NAMING_CONFIG_PATH = naming_path
    result = cm.map_columns(["Customer$ID"], {})
    assert result == ["customer_id"], f"Expected ['customer_id'], got {result}"
    naming_path.unlink(missing_ok=True)


# ============================================================
# TEST K — override precedence
# ============================================================

def test_override_precedence_over_style():
    import scripts.python.common.column_mapper as cm
    import tempfile

    naming_rules = {
        "version": "1.0",
        "settings": {"enable_naming_engine": True},
        "table": {"style": "snake_case", "character_replacements": {}, "overrides": {}},
        "column": {
            "style": "snake_case",
            "character_replacements": {},
            "overrides": {"Customer ID": "customerIdentifier"},
        },
        "collision": {"strategy": "suffix", "separator": "_", "start_index": 2},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(naming_rules, f)
        naming_path = Path(f.name)

    cm.NAMING_CONFIG_PATH = naming_path
    result = cm.map_columns(["Customer ID"], {})
    assert result == ["customerIdentifier"], f"Expected ['customerIdentifier'], got {result}"
    naming_path.unlink(missing_ok=True)


# ============================================================
# TEST — collision handling
# ============================================================

def test_collision_suffix_in_schema_flow():
    import scripts.python.common.column_mapper as cm
    import tempfile

    naming_rules = {
        "version": "1.0",
        "settings": {"enable_naming_engine": True},
        "table": {"style": "snake_case", "character_replacements": {}, "overrides": {}},
        "column": {
            "style": "snake_case",
            "character_replacements": {" ": "_", "-": "_"},
            "overrides": {},
        },
        "collision": {"strategy": "suffix", "separator": "_", "start_index": 2},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(naming_rules, f)
        naming_path = Path(f.name)

    cm.NAMING_CONFIG_PATH = naming_path
    result = cm.map_columns(["Customer-ID", "Customer_ID", "Customer ID"], {})
    assert result == ["customer_id", "customer_id_2", "customer_id_3"]
    naming_path.unlink(missing_ok=True)


def test_collision_fail_in_schema_flow():
    import scripts.python.common.column_mapper as cm
    import tempfile

    naming_rules = {
        "version": "1.0",
        "settings": {"enable_naming_engine": True},
        "table": {"style": "snake_case", "character_replacements": {}, "overrides": {}},
        "column": {
            "style": "snake_case",
            "character_replacements": {" ": "_", "-": "_"},
            "overrides": {},
        },
        "collision": {"strategy": "fail", "separator": "_", "start_index": 2},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(naming_rules, f)
        naming_path = Path(f.name)

    cm.NAMING_CONFIG_PATH = naming_path
    with pytest.raises(cm.CollisionError):
        cm.map_columns(["Customer-ID", "Customer_ID"], {})
    naming_path.unlink(missing_ok=True)


# ============================================================
# TEST — source file integrity
# ============================================================

def test_source_file_not_renamed(tmp_path):
    incoming = tmp_path / "incoming" / "mysql"
    incoming.mkdir(parents=True, exist_ok=True)
    source_file = incoming / "Customer Records.csv"
    write_csv(
        source_file,
        ["CustomerID", "FirstName"],
        [["1", "John"]],
    )

    naming_rules = {
        "version": "1.0",
        "settings": {"enable_naming_engine": True},
        "table": {
            "style": "snake_case",
            "character_replacements": {" ": "_"},
            "overrides": {"Customer Records": "customers"},
        },
        "column": {
            "style": "snake_case",
            "character_replacements": {},
            "overrides": {"CustomerID": "customer_id"},
        },
        "collision": {"strategy": "suffix", "separator": "_", "start_index": 2},
    }
    naming_path = tmp_path / "naming_rules.json"
    with open(naming_path, "w", encoding="utf-8") as f:
        json.dump(naming_rules, f)

    import scripts.python.common.column_mapper as cm
    cm.NAMING_CONFIG_PATH = naming_path

    registry, table_source_mapping, results = run_schema_detection(
        tmp_path, enable_naming_engine=True
    )

    assert source_file.exists()
    assert table_source_mapping["customers"] == "Customer Records"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
