import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.schema_editor import app as editor


def test_mssql_editor_rejects_bare_varchar_before_persisting_contract():
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry = Path(tmp_dir) / "datatype_registry.json"
        registry.write_text(json.dumps({"orders": {"order_id": {"selected_type": "INTEGER"}}}), encoding="utf-8")
        with patch.object(editor, "DATA_FILE", registry), patch.object(editor, "DATABASE", "mssql"), patch.object(editor.threading, "Timer"):
            editor.app.config["TESTING"] = True
            response = editor.app.test_client().post("/save", data={"orders__order_id": "VARCHAR"})
        assert response.status_code == 400
        assert json.loads(registry.read_text(encoding="utf-8"))["orders"]["order_id"]["selected_type"] == "INTEGER"


def test_mssql_editor_accepts_explicit_varchar_values_without_rewriting_them():
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry = Path(tmp_dir) / "datatype_registry.json"
        registry.write_text(json.dumps({"orders": {"order_id": {"selected_type": "INTEGER"}}}), encoding="utf-8")
        timer = MagicMock()
        with patch.object(editor, "DATA_FILE", registry), patch.object(editor, "DATABASE", "mssql"), patch.object(editor.threading, "Timer", return_value=timer):
            editor.app.config["TESTING"] = True
            response = editor.app.test_client().post("/save", data={"orders__order_id": "VARCHAR(255)"})
        assert response.status_code == 200
        assert json.loads(registry.read_text(encoding="utf-8"))["orders"]["order_id"]["selected_type"] == "VARCHAR(255)"
        timer.start.assert_called_once()


def test_mssql_editor_renders_varchar_max_for_text_detected_type():
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry = Path(tmp_dir) / "datatype_registry.json"
        registry.write_text(json.dumps({
            "orders": {
                "order_id": {
                    "detected_type": "TEXT",
                    "selected_type": "TEXT",
                }
            }
        }), encoding="utf-8")
        with patch.object(editor, "DATA_FILE", registry), patch.object(editor, "DATABASE", "mssql"):
            editor.app.config["TESTING"] = True
            response = editor.app.test_client().get("/")
        assert response.status_code == 200
        assert 'value="VARCHAR(MAX)"' in response.data.decode()


def test_mssql_editor_normalizes_bare_varchar_using_detected_type():
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry = Path(tmp_dir) / "datatype_registry.json"
        registry.write_text(json.dumps({
            "orders": {
                "order_id": {
                    "detected_type": "TEXT",
                    "selected_type": "VARCHAR",
                }
            }
        }), encoding="utf-8")
        with patch.object(editor, "DATA_FILE", registry), patch.object(editor, "DATABASE", "mssql"):
            editor.app.config["TESTING"] = True
            response = editor.app.test_client().get("/")
        assert response.status_code == 200
        assert 'value="VARCHAR(MAX)"' in response.data.decode()


def test_mssql_editor_preserves_explicit_varchar255():
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry = Path(tmp_dir) / "datatype_registry.json"
        registry.write_text(json.dumps({
            "orders": {
                "order_id": {
                    "detected_type": "TEXT",
                    "selected_type": "VARCHAR(255)",
                }
            }
        }), encoding="utf-8")
        with patch.object(editor, "DATA_FILE", registry), patch.object(editor, "DATABASE", "mssql"):
            editor.app.config["TESTING"] = True
            response = editor.app.test_client().get("/")
        assert response.status_code == 200
        assert 'value="VARCHAR(255)"' in response.data.decode()


def test_mssql_editor_preserves_varchar_max():
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry = Path(tmp_dir) / "datatype_registry.json"
        registry.write_text(json.dumps({
            "orders": {
                "order_id": {
                    "detected_type": "TEXT",
                    "selected_type": "VARCHAR(MAX)",
                }
            }
        }), encoding="utf-8")
        with patch.object(editor, "DATA_FILE", registry), patch.object(editor, "DATABASE", "mssql"):
            editor.app.config["TESTING"] = True
            response = editor.app.test_client().get("/")
        assert response.status_code == 200
        assert 'value="VARCHAR(MAX)"' in response.data.decode()


def test_mssql_editor_save_with_normalized_initial_value_succeeds():
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry = Path(tmp_dir) / "datatype_registry.json"
        registry.write_text(json.dumps({
            "orders": {
                "order_id": {
                    "detected_type": "TEXT",
                    "selected_type": "TEXT",
                }
            }
        }), encoding="utf-8")
        timer = MagicMock()
        with patch.object(editor, "DATA_FILE", registry), patch.object(editor, "DATABASE", "mssql"), patch.object(editor.threading, "Timer", return_value=timer):
            editor.app.config["TESTING"] = True
            response = editor.app.test_client().get("/")
            assert response.status_code == 200
            assert 'value="VARCHAR(MAX)"' in response.data.decode()

            response = editor.app.test_client().post("/save", data={"orders__order_id": "VARCHAR(MAX)"})
            assert response.status_code == 200
            assert json.loads(registry.read_text(encoding="utf-8"))["orders"]["order_id"]["selected_type"] == "VARCHAR(MAX)"
            timer.start.assert_called_once()


from scripts.datatype_registry_generator import resolve_registry_datatype


def test_mssql_registry_regeneration_preserves_user_selected_varchar_max_for_text():
    existing = {
        "detected_type": "TEXT",
        "selected_type": "VARCHAR(MAX)",
        "final_type": "VARCHAR(MAX)",
    }
    assert resolve_registry_datatype(existing, "TEXT") == "VARCHAR(MAX)"


def test_mssql_registry_regeneration_preserves_user_selected_varchar255_for_text():
    existing = {
        "detected_type": "TEXT",
        "selected_type": "VARCHAR(255)",
        "final_type": "VARCHAR(255)",
    }
    assert resolve_registry_datatype(existing, "TEXT") == "VARCHAR(255)"


def test_mssql_registry_regeneration_keeps_decimal_and_bit_values():
    for value in ("DECIMAL(12,2)", "BIT"):
        existing = {
            "detected_type": "NUMERIC",
            "selected_type": value,
            "final_type": value,
        }
        assert resolve_registry_datatype(existing, "NUMERIC") == value


def test_mssql_datatype_validator_rejects_bare_varchar():
    from scripts.python.common.mssql_datatype_validation import validate_mssql_datatype

    try:
        validate_mssql_datatype("VARCHAR")
    except ValueError:
        pass
    else:
        raise AssertionError("bare VARCHAR should be rejected")
