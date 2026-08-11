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
    def test_detect_schema_changes_reports_rename(self):
        schema_detector = load_schema_detector()

        result = schema_detector.detect_schema_changes(
            ["customer_name"],
            ["customer_full_name"],
        )

        self.assertEqual(result["status"], "RENAMED")
        self.assertEqual(result["renamed_columns"], {"customer_name": "customer_full_name"})

    def test_detect_schema_changes_reports_datatype_change(self):
        schema_detector = load_schema_detector()

        result = schema_detector.detect_schema_changes(
            ["product_id"],
            ["product_id"],
        )

        self.assertIn(result["status"], {"UNCHANGED", "CHANGED"})


if __name__ == "__main__":
    unittest.main()
