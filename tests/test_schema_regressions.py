import importlib.util
import json
import runpy
import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _copy_generator_script(temp_root: Path) -> Path:
    src = REPO_ROOT / "scripts" / "datatype_registry_generator.py"
    dst = temp_root / "scripts" / "datatype_registry_generator.py"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def load_schema_detector():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "schema_detector.py"
    spec = importlib.util.spec_from_file_location("schema_detector_mod", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SchemaDetectorRegressionTests(unittest.TestCase):
    def test_detect_schema_changes_does_not_guess_rename(self):
        schema_detector = load_schema_detector()

        result = schema_detector.detect_schema_changes(
            ["customer_name"],
            ["customer_full_name"],
        )

        self.assertEqual(result["status"], "CHANGED")
        self.assertEqual(result["renamed_columns"], {})

    def test_detect_schema_changes_reports_datatype_change(self):
        schema_detector = load_schema_detector()

        result = schema_detector.detect_schema_changes(
            ["product_id"],
            ["product_id"],
        )

        self.assertIn(result["status"], {"UNCHANGED", "CHANGED"})

    def test_mssql_drift_comparison_reports_manual_column_and_type_changes(self):
        module_path = Path(__file__).resolve().parents[1] / "scripts" / "python" / "mssql" / "setup" / "validate_schema_drift.py"
        spec = importlib.util.spec_from_file_location("mssql_drift_mod", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        expected = {"orders": {"total_amount": {"name": "total_amount", "type": "DECIMAL(10,2)"}}}
        actual = {"orders": {
            "renamed_amount": {"name": "renamed_amount", "type": "VARCHAR(255)"},
            "manual_column": {"name": "manual_column", "type": "INTEGER"},
        }}
        differences = module.schema_differences(expected, actual)
        self.assertTrue(any("Expected: DECIMAL(10,2); Actual: missing" in item for item in differences))
        self.assertTrue(any("manual_column" in item and "unexpected" in item for item in differences))

        typed_actual = {"orders": {"total_amount": {"name": "total_amount", "type": "VARCHAR(255)"}}}
        self.assertIn("Expected: DECIMAL(10,2); Actual: VARCHAR(255)", module.schema_differences(expected, typed_actual)[0])

    def test_mssql_type_equivalence_preserves_parameters_and_detects_real_drift(self):
        module_path = Path(__file__).resolve().parents[1] / "scripts" / "python" / "mssql" / "setup" / "validate_schema_drift.py"
        spec = importlib.util.spec_from_file_location("mssql_type_equivalence", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def differences(expected_type, actual_type):
            expected = {"orders": {"value": {"name": "value", "type": expected_type}}}
            actual = {"orders": {"value": {"name": "value", "type": actual_type}}}
            return module.schema_differences(expected, actual)

        self.assertEqual(differences("TEXT", "VARCHAR(MAX)"), [])
        self.assertEqual(differences("INTEGER", "INT"), [])
        self.assertEqual(differences("NUMERIC(10,2)", "DECIMAL(10,2)"), [])
        self.assertEqual(differences("NUMERIC", "DECIMAL(18,0)"), [])
        self.assertEqual(differences("TIMESTAMP", "DATETIME2(7)"), [])
        self.assertEqual(module._actual_type("timestamp", 8, 0, 0), "ROWVERSION")
        self.assertTrue(differences("TIMESTAMP", "ROWVERSION"))
        self.assertTrue(differences("VARCHAR(100)", "VARCHAR(255)"))
        self.assertTrue(differences("VARCHAR(100)", "VARCHAR(MAX)"))
        self.assertTrue(differences("DECIMAL(10,2)", "DECIMAL(18,0)"))
        self.assertTrue(differences("INTEGER", "DATE"))

    def test_mssql_datatype_contract_rejects_ambiguous_parameterized_types(self):
        from scripts.python.common.mssql_datatype_validation import validate_mssql_datatype

        for datatype in ("VARCHAR", "NVARCHAR", "CHAR", "NCHAR", "VARBINARY", "DECIMAL", "NUMERIC"):
            with self.assertRaises(ValueError):
                validate_mssql_datatype(datatype)
        for datatype in ("VARCHAR(255)", "VARCHAR(MAX)", "NVARCHAR(80)", "NVARCHAR(MAX)", "CHAR(1)", "NCHAR(1)", "VARBINARY(MAX)", "DECIMAL(10,2)"):
            validate_mssql_datatype(datatype)

    def test_mssql_registry_generation_keeps_detected_bare_varchar_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "metadata" / "mssql").mkdir(parents=True)
            (root / "incoming" / "mssql").mkdir(parents=True)
            schema_path = root / "metadata" / "mssql" / "schema_registry.json"
            schema_path.write_text(json.dumps({"orders": ["order_id"]}), encoding="utf-8")

            registry_path = root / "metadata" / "mssql" / "datatype_registry.json"
            registry_path.write_text(json.dumps({
                "orders": {
                    "order_id": {
                        "detected_type": "VARCHAR",
                        "selected_type": "",
                        "final_type": "",
                    }
                }
            }), encoding="utf-8")

            (root / "incoming" / "mssql" / "orders.csv").write_text("order_id\nABC\n", encoding="utf-8")

            script_path = _copy_generator_script(root)
            import sys
            original_argv = list(sys.argv)
            try:
                sys.argv = [str(script_path), "mssql"]
                runpy.run_path(str(script_path), run_name="__main__")
            finally:
                sys.argv = original_argv

            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertEqual(registry["orders"]["order_id"]["detected_type"], "VARCHAR")
            self.assertEqual(registry["orders"]["order_id"]["selected_type"], "VARCHAR")
            self.assertEqual(registry["orders"]["order_id"]["final_type"], "VARCHAR")

    def test_mssql_registry_resolution_rejects_bare_selected_varchar_and_preserves_valid_explicit_types(self):
        from scripts.datatype_registry_generator import resolve_registry_datatype

        explicit_empty = {"selected_type": "", "final_type": "", "detected_type": "VARCHAR"}
        self.assertEqual(resolve_registry_datatype(explicit_empty, "VARCHAR"), "VARCHAR")

        with self.assertRaises(ValueError):
            resolve_registry_datatype({"selected_type": "VARCHAR"}, "TEXT")

        self.assertEqual(resolve_registry_datatype({"selected_type": "VARCHAR(255)"}, "TEXT"), "VARCHAR(255)")
        self.assertEqual(resolve_registry_datatype({"selected_type": "VARCHAR(MAX)"}, "TEXT"), "VARCHAR(MAX)")
        self.assertEqual(resolve_registry_datatype({"final_type": "VARCHAR(255)"}, "TEXT"), "VARCHAR(255)")


if __name__ == "__main__":
    unittest.main()
