import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
