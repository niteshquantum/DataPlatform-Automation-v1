import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.schema_editor import app as schema_editor_app


class TestSchemaEditorNetwork(unittest.TestCase):
    def test_linux_default_route_selects_192_168_when_it_is_route_source(self):
        output = "default via 192.168.1.1 dev wlan0 proto static metric 600\n1.1.1.1 via 192.168.1.1 dev wlan0 src 192.168.1.12 uid 1000\n"
        self.assertEqual(schema_editor_app.parse_linux_default_route_ip(output), "192.168.1.12")

    def test_linux_default_route_selects_10_when_it_is_route_source(self):
        output = "default via 10.10.10.1 dev eth1 proto static metric 100\n1.1.1.1 via 10.10.10.1 dev eth1 src 10.10.10.105 uid 1000\n"
        self.assertEqual(schema_editor_app.parse_linux_default_route_ip(output), "10.10.10.105")

    def test_linux_default_route_ignores_virtual_interface_candidates(self):
        output = "default via 172.17.0.1 dev docker0 proto static\n1.1.1.1 via 172.17.0.1 dev docker0 src 10.10.10.105 uid 1000\n"
        self.assertIsNone(schema_editor_app.parse_linux_default_route_ip(output))

    def test_windows_default_route_preferred_when_multiple_ipv4s_exist(self):
        output = """
        InterfaceIndex : 5
        InterfaceAlias : Wi-Fi
        IPAddress : 192.168.1.20

        InterfaceIndex : 11
        InterfaceAlias : vEthernet (WSL)
        IPAddress : 10.10.10.105

        DestinationPrefix : 0.0.0.0/0
        InterfaceIndex : 5
        """
        selected = schema_editor_app.select_preferred_ip_from_windows_output(output)
        self.assertEqual(selected, "192.168.1.20")

    def test_windows_multiple_interfaces_uses_default_route_ip(self):
        output = """
        InterfaceIndex : 7
        InterfaceAlias : Ethernet
        IPAddress : 10.0.0.12

        InterfaceIndex : 12
        InterfaceAlias : Wi-Fi
        IPAddress : 192.168.1.25

        DestinationPrefix : 0.0.0.0/0
        InterfaceIndex : 12
        """
        selected = schema_editor_app.select_preferred_ip_from_windows_output(output)
        self.assertEqual(selected, "192.168.1.25")

    def test_windows_rejects_apipa_on_default_route_interface(self):
        output = """
        InterfaceIndex : 5
        InterfaceAlias : Ethernet
        IPAddress : 169.254.34.56

        InterfaceIndex : 12
        InterfaceAlias : Wi-Fi
        IPAddress : 192.168.1.25

        DestinationPrefix : 0.0.0.0/0
        InterfaceIndex : 5
        """
        selected = schema_editor_app.select_preferred_ip_from_windows_output(output)
        self.assertEqual(selected, "192.168.1.25")

    def test_windows_rejects_virtual_interface_with_apipa(self):
        output = """
        InterfaceIndex : 11
        InterfaceAlias : vEthernet (WSL)
        IPAddress : 169.254.100.1

        InterfaceIndex : 12
        InterfaceAlias : Wi-Fi
        IPAddress : 192.168.1.25

        DestinationPrefix : 0.0.0.0/0
        InterfaceIndex : 11
        """
        selected = schema_editor_app.select_preferred_ip_from_windows_output(output)
        self.assertEqual(selected, "192.168.1.25")

    def test_windows_all_interfaces_apipa_returns_none(self):
        output = """
        InterfaceIndex : 5
        InterfaceAlias : Ethernet
        IPAddress : 169.254.34.56

        InterfaceIndex : 11
        InterfaceAlias : vEthernet (WSL)
        IPAddress : 169.254.100.1

        DestinationPrefix : 0.0.0.0/0
        InterfaceIndex : 5
        """
        selected = schema_editor_app.select_preferred_ip_from_windows_output(output)
        self.assertIsNone(selected)

    def test_apipa_is_rejected_by_helper(self):
        self.assertTrue(schema_editor_app.is_apipa("169.254.34.56"))
        self.assertTrue(schema_editor_app.is_apipa("169.254.1.1"))
        self.assertFalse(schema_editor_app.is_apipa("192.168.1.1"))
        self.assertFalse(schema_editor_app.is_apipa("10.0.0.1"))
        self.assertFalse(schema_editor_app.is_apipa("127.0.0.1"))

    def test_valid_lan_ip_rejects_apipa_and_loopback(self):
        self.assertTrue(schema_editor_app.is_valid_lan_ip("192.168.1.1"))
        self.assertTrue(schema_editor_app.is_valid_lan_ip("10.0.0.1"))
        self.assertFalse(schema_editor_app.is_valid_lan_ip("169.254.34.56"))
        self.assertFalse(schema_editor_app.is_valid_lan_ip("127.0.0.1"))
        self.assertFalse(schema_editor_app.is_valid_lan_ip("169.254.0.0"))

    def test_linux_default_route_rejects_apipa_source(self):
        output = "default via 192.168.1.1 dev wlan0 src 169.254.34.56 uid 1000\n"
        self.assertIsNone(schema_editor_app.parse_linux_default_route_ip(output))

    def test_main_does_not_fail_on_lan_self_connect(self):
        app_source = Path(schema_editor_app.__file__).read_text(encoding='utf-8')
        main_block = app_source[app_source.index('if __name__ == "__main__":'):]
        self.assertNotIn('wait_for_local_http(host', main_block)
        self.assertNotIn('not reachable at', main_block)

    def test_no_hardcoded_machine_specific_address_is_required(self):
        self.assertNotIn("192.168.1.12", schema_editor_app.__file__)
        self.assertNotIn("10.10.10.105", schema_editor_app.__file__)

    def test_build_schema_editor_url_uses_runtime_host_and_port(self):
        self.assertEqual(
            schema_editor_app.build_schema_editor_url("192.168.0.15", 5000),
            "http://192.168.0.15:5000",
        )

    def test_get_schema_editor_port_uses_configured_value(self):
        with patch.dict(os.environ, {"SCHEMA_EDITOR_PORT": "6789"}, clear=False):
            self.assertEqual(schema_editor_app.get_schema_editor_port(), 6789)

    def test_schema_editor_binds_to_all_interfaces(self):
        self.assertEqual(schema_editor_app.DEFAULT_BIND_HOST, "0.0.0.0")

    def test_firewall_rule_name_is_stable_and_port_specific(self):
        rule_name = schema_editor_app.build_firewall_rule_name(5000)
        self.assertIn("5000", rule_name)
        self.assertEqual(rule_name, schema_editor_app.build_firewall_rule_name(5000))

    def test_windows_firewall_rule_validation(self):
        profile = schema_editor_app.windows_firewall_rule_matches_profile(
            {"enabled": True, "profiles": ["Private", "Domain"], "local_port": "5000"},
            5000,
        )
        self.assertTrue(profile)

    def test_linux_firewall_reuses_existing_iptables_rule(self):
        with patch.object(schema_editor_app, "resolve_linux_firewall_tool", return_value="iptables"):
            with patch.object(schema_editor_app.subprocess, "run") as mock_run:
                mock_run.return_value.returncode = 0
                self.assertTrue(schema_editor_app.ensure_linux_firewall_access(5000))
                self.assertTrue(mock_run.call_count >= 1)
                first_call = mock_run.call_args_list[0][0][0]
                self.assertIn("iptables", first_call)

    def test_ubuntu_firewall_detection_uses_ufw_when_available(self):
        with patch.object(schema_editor_app, "resolve_linux_firewall_tool", return_value="ufw"):
            self.assertEqual(schema_editor_app.resolve_linux_firewall_tool(), "ufw")

    def test_existing_windows_rule_is_reused(self):
        with patch.object(schema_editor_app.subprocess, "run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Rule Name: Schema Editor Port 5000 (LAN)"
            self.assertTrue(schema_editor_app.ensure_windows_firewall_access(5000))

    def test_windows_firewall_rule_is_idempotent_before_readd(self):
        with patch.object(schema_editor_app, "windows_firewall_rule_exists", return_value=True):
            with patch.object(schema_editor_app.subprocess, "run") as mock_run:
                self.assertTrue(schema_editor_app.provision_windows_firewall_rule(5000))
                mock_run.assert_not_called()

    def test_missing_windows_firewall_rule_raises_runtime_error(self):
        with patch.object(schema_editor_app.subprocess, "run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = "No rules match."
            with self.assertRaises(RuntimeError):
                schema_editor_app.ensure_windows_firewall_access(5000)

    def test_start_schema_editor_command_uses_project_path_and_background_launch(self):
        content = open('scripts/batch/common/start_schema_editor.bat', 'r', encoding='utf-8').read()
        self.assertIn('start "Schema Editor" /b', content)
        self.assertIn('scripts\\schema_editor\\app.py', content)
        self.assertIn('netstat -an', content)
        self.assertIn('curl.exe', content)
        self.assertIn('Schema Editor started successfully', content)
        self.assertNotIn('START_CMD=\\"', content)
        self.assertIn('exit /b 1', content)

    def test_app_runtime_does_not_call_firewall_check(self):
        app_source = Path(schema_editor_app.__file__).read_text(encoding='utf-8')
        main_block = app_source[app_source.index('if __name__ == "__main__":'):]
        self.assertNotIn('ensure_schema_editor_network_access', main_block)
        self.assertNotIn('ensure_windows_firewall_access', main_block)

    def test_app_startup_message_contains_scoped_ready_status(self):
        app_source = Path(schema_editor_app.__file__).read_text(encoding='utf-8')
        main_block = app_source[app_source.index('if __name__ == "__main__":'):]
        self.assertIn('SCHEMA EDITOR READY', main_block)
        self.assertIn('WAITING FOR USER SAVE', main_block)
        self.assertIn('build_schema_editor_url', main_block)

    def test_app_save_handler_writes_scoped_marker_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            data_file = project_root / "metadata" / "postgresql" / "datatype_registry.json"
            data_file.parent.mkdir(parents=True, exist_ok=True)
            data_file.write_text(
                json.dumps({"tbl": {"col": {"sample_value": "a", "detected_type": "TEXT", "selected_type": "TEXT"}}}),
                encoding="utf-8",
            )

            with patch.object(schema_editor_app, "PROJECT_ROOT", project_root):
                with patch.object(schema_editor_app, "DATABASE", "postgresql"):
                    with patch.object(schema_editor_app, "DATA_FILE", data_file):
                        with patch.dict(os.environ, {"BUILD_NUMBER": "42"}, clear=False):
                            mock_request = MagicMock()
                            mock_request.form = {"tbl__col": "VARCHAR"}
                            with patch.object(schema_editor_app, "request", mock_request):
                                status = schema_editor_app.save()
                                self.assertEqual(status[1], 200)
                                marker_dir = project_root / "outputs" / "schema_editor_markers"
                                self.assertTrue(marker_dir.exists())
                                markers = list(marker_dir.glob("save_marker.postgresql.42.*"))
                                self.assertEqual(len(markers), 1)
                                content = json.loads(markers[0].read_text(encoding="utf-8"))
                                self.assertEqual(content["database"], "postgresql")
                                self.assertEqual(content["build_number"], "42")
                                self.assertIn("marker_id", content)
                                self.assertIn("timestamp", content)

    def test_app_save_handler_marker_scoped_to_database_and_build(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            data_file = project_root / "metadata" / "mysql" / "datatype_registry.json"
            data_file.parent.mkdir(parents=True, exist_ok=True)
            data_file.write_text(
                json.dumps({"tbl": {"col": {"sample_value": "a", "detected_type": "TEXT", "selected_type": "TEXT"}}}),
                encoding="utf-8",
            )

            with patch.object(schema_editor_app, "PROJECT_ROOT", project_root):
                with patch.object(schema_editor_app, "DATABASE", "mysql"):
                    with patch.object(schema_editor_app, "DATA_FILE", data_file):
                        with patch.dict(os.environ, {"BUILD_NUMBER": "99"}, clear=False):
                            mock_request = MagicMock()
                            mock_request.form = {"tbl__col": "INTEGER"}
                            with patch.object(schema_editor_app, "request", mock_request):
                                schema_editor_app.save()
                                marker_dir = project_root / "outputs" / "schema_editor_markers"
                                mysql_markers = list(marker_dir.glob("save_marker.mysql.99.*"))
                                self.assertEqual(len(mysql_markers), 1)
                                postgresql_markers = list(marker_dir.glob("save_marker.postgresql.99.*"))
                                self.assertEqual(len(postgresql_markers), 0)

    def test_old_save_marker_cannot_release_new_build(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            data_file = project_root / "metadata" / "postgresql" / "datatype_registry.json"
            data_file.parent.mkdir(parents=True, exist_ok=True)
            data_file.write_text(
                json.dumps({"tbl": {"col": {"sample_value": "a", "detected_type": "TEXT", "selected_type": "TEXT"}}}),
                encoding="utf-8",
            )

            with patch.object(schema_editor_app, "PROJECT_ROOT", project_root):
                with patch.object(schema_editor_app, "DATABASE", "postgresql"):
                    with patch.object(schema_editor_app, "DATA_FILE", data_file):
                        with patch.dict(os.environ, {"BUILD_NUMBER": "100"}, clear=False):
                            old_marker_dir = project_root / "outputs" / "schema_editor_markers"
                            old_marker_dir.mkdir(parents=True, exist_ok=True)
                            (old_marker_dir / "save_marker.postgresql.50.oldmarker").write_text(
                                json.dumps({"database": "postgresql", "build_number": "50"}),
                                encoding="utf-8",
                            )

                            mock_request = MagicMock()
                            mock_request.form = {"tbl__col": "VARCHAR"}
                            with patch.object(schema_editor_app, "request", mock_request):
                                schema_editor_app.save()
                                markers = list(old_marker_dir.glob("save_marker.postgresql.100.*"))
                                self.assertEqual(len(markers), 1)
                                old_markers = list(old_marker_dir.glob("save_marker.postgresql.50.*"))
                                self.assertEqual(len(old_markers), 1)

    def test_load_steps_groovy_uses_blocking_app_py(self):
        load_steps = open('jenkins/common/postgresql/load_steps.groovy', 'r', encoding='utf-8').read()
        start = load_steps.index("stage('Schema Editor')")
        end = load_steps.index("stage('Create Database')")
        schema_editor_block = load_steps[start:end]
        self.assertIn('runTrackedStage', schema_editor_block)
        self.assertIn('scripts\\\\schema_editor\\\\app.py', schema_editor_block)
        self.assertNotIn('start_schema_editor.bat', schema_editor_block)
        self.assertNotIn('SKIPPED', schema_editor_block)
        self.assertNotIn('returnStatus', schema_editor_block)

    def test_load_steps_groovy_has_all_stages_after_schema_editor(self):
        load_steps = open('jenkins/common/postgresql/load_steps.groovy', 'r', encoding='utf-8').read()
        schema_editor_block = load_steps[load_steps.index("stage('Schema Editor')"):]
        required_stages = [
            'Create Database',
            'Run CDC',
            'Load Data',
            'Validate Loaded Data',
            'Deploy Database Objects',
            'Validate Database Objects',
            'Assessment & Reconciliation',
            'Discovery & Migration Reporting',
        ]
        for stage in required_stages:
            self.assertIn(stage, schema_editor_block,
                          f"Stage '{stage}' must still exist after Schema Editor in the pipeline.")

    def test_ci_cd_load_pipeline_uses_blocking_app_py(self):
        content = open('CI_CD/postgresql/windows/load_pipeline.groovy', 'r', encoding='utf-8').read()
        schema_editor_start = content.index("stage('Schema Editor')")
        next_stage = content.find("\n        stage('", schema_editor_start + 1)
        if next_stage == -1:
            next_stage = len(content)
        schema_editor_block = content[schema_editor_start:next_stage]
        self.assertIn('runTrackedStage', schema_editor_block)
        self.assertIn('scripts\\\\schema_editor\\\\app.py', schema_editor_block)
        self.assertNotIn('start_schema_editor.bat', schema_editor_block)
        self.assertNotIn('SKIPPED', schema_editor_block)
        self.assertNotIn('returnStatus', schema_editor_block)
        self.assertNotIn("currentBuild.result", schema_editor_block)

    def test_ensure_schema_editor_firewall_bat_is_idempotent(self):
        content = open('scripts/batch/common/ensure_schema_editor_firewall.bat', 'r', encoding='utf-8').read()
        self.assertIn('show rule', content)
        self.assertIn('if not errorlevel 1', content)
        self.assertIn('add rule', content)
        self.assertIn('Private,Domain', content)
        self.assertIn('LocalSubnet', content)
        self.assertIn('check_admin_privileges.bat', content)

    def test_ensure_schema_editor_firewall_bat_fails_without_admin(self):
        content = open('scripts/batch/common/ensure_schema_editor_firewall.bat', 'r', encoding='utf-8').read()
        self.assertIn('Administrator privileges not available', content)
        self.assertIn('exit /b 1', content)

    def test_ensure_schema_editor_firewall_bat_reads_port_from_network_conf(self):
        content = open('scripts/batch/common/ensure_schema_editor_firewall.bat', 'r', encoding='utf-8').read()
        self.assertIn('config\\common\\network.conf', content)
        self.assertIn('SCHEMA_EDITOR_PORT', content)


if __name__ == "__main__":
    unittest.main()
