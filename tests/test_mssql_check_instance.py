import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestCheckInstance(unittest.TestCase):

    def setUp(self):
        self.instance = "DMSQL"
        self.service_name = "MSSQL$DMSQL"
        self.host = "localhost"
        self.port = 1533
        self.config = {
            "MSSQL_HOST": self.host,
            "MSSQL_PORT": str(self.port),
            "MSSQL_INSTANCE": self.instance,
        }

    def _run_check(self):
        from scripts.python.mssql.setup.check_instance import check_instance
        return check_instance()

    def test_scenario_1_running_managed_instance(self):
        """Correct managed instance running -> INSTANCE_RUNNING_AND_USABLE."""
        with patch(
            "scripts.python.mssql.setup.check_instance.load_database_config",
            return_value=self.config,
        ), patch(
            "scripts.python.mssql.setup.check_instance.subprocess.run"
        ) as mock_run, patch(
            "scripts.python.mssql.setup.check_instance.socket.socket"
        ) as mock_socket_class:

            mock_socket = MagicMock()
            mock_socket.connect_ex.return_value = 0
            mock_socket_class.return_value = mock_socket
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="Running"),
                MagicMock(
                    returncode=0,
                    stdout="        BINARY_PATH_NAME   : "
                           "\"C:\\Program Files\\Microsoft SQL Server\\"
                           "MSSQL16.DMSQL\\MSSQL\\Binn\\sqlservr.exe\" -sDMSQL",
                ),
                MagicMock(returncode=0, stdout="MSSQL16.DMSQL"),
                MagicMock(
                    returncode=0,
                    stdout="C:\\Program Files\\Microsoft SQL Server\\"
                           "MSSQL16.DMSQL\\MSSQL\\Binn\\sqlservr.exe -sDMSQL",
                ),
            ]

            state = self._run_check()
            self.assertEqual(state, "INSTANCE_RUNNING_AND_USABLE")

    def test_scenario_2_stopped_managed_instance(self):
        """Correct managed instance stopped -> INSTANCE_INSTALLED_BUT_STOPPED."""
        with patch(
            "scripts.python.mssql.setup.check_instance.load_database_config",
            return_value=self.config,
        ), patch(
            "scripts.python.mssql.setup.check_instance.subprocess.run"
        ) as mock_run, patch(
            "scripts.python.mssql.setup.check_instance.socket.socket"
        ) as mock_socket_class:

            mock_socket = MagicMock()
            mock_socket.connect_ex.return_value = 0
            mock_socket_class.return_value = mock_socket
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="Stopped"),
                MagicMock(
                    returncode=0,
                    stdout="        BINARY_PATH_NAME   : "
                           "\"C:\\Program Files\\Microsoft SQL Server\\"
                           "MSSQL16.DMSQL\\MSSQL\\Binn\\sqlservr.exe\" -sDMSQL",
                ),
                MagicMock(returncode=0, stdout="MSSQL16.DMSQL"),
                MagicMock(
                    returncode=0,
                    stdout="C:\\Program Files\\Microsoft SQL Server\\"
                           "MSSQL16.DMSQL\\MSSQL\\Binn\\sqlservr.exe -sDMSQL",
                ),
            ]

            state = self._run_check()
            self.assertEqual(state, "INSTANCE_INSTALLED_BUT_STOPPED")

    def test_scenario_3_foreign_instance_same_service_name(self):
        """Foreign instance with same service name/port -> NOT accepted."""
        with patch(
            "scripts.python.mssql.setup.check_instance.load_database_config",
            return_value=self.config,
        ), patch(
            "scripts.python.mssql.setup.check_instance.subprocess.run"
        ) as mock_run, patch(
            "scripts.python.mssql.setup.check_instance.socket.socket"
        ) as mock_socket_class:

            mock_socket = MagicMock()
            mock_socket.connect_ex.return_value = 0
            mock_socket_class.return_value = mock_socket
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="Running"),
                MagicMock(
                    returncode=0,
                    stdout="        BINARY_PATH_NAME   : "
                           "C:\\some\\foreign\\path\\fake.exe",
                ),
                MagicMock(returncode=0, stdout=""),
                MagicMock(returncode=0, stdout=""),
            ]

            state = self._run_check()
            self.assertEqual(state, "NO_INSTANCE")

    def test_scenario_4_no_instance(self):
        """No instance -> NO_INSTANCE."""
        with patch(
            "scripts.python.mssql.setup.check_instance.load_database_config",
            return_value=self.config,
        ), patch(
            "scripts.python.mssql.setup.check_instance.subprocess.run",
            return_value=MagicMock(returncode=1, stdout=""),
        ):

            state = self._run_check()
            self.assertEqual(state, "NO_INSTANCE")


if __name__ == "__main__":
    unittest.main()
