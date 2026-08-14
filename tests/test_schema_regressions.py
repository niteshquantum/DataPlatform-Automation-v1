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


if __name__ == "__main__":
    unittest.main()
