import importlib.util
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
