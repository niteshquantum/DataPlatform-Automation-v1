from pathlib import Path
import sys
import socket
import subprocess
from pymongo import MongoClient
from pymongo.errors import PyMongoError

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.mongodb.setup.config_loader import load_config

config = load_config()

HOST = config["MONGODB_HOST"]
PORT = int(config["MONGODB_PORT"])
DB = config["MONGODB_DATABASE"]

PROJECT_MONGOD_BIN = ROOT / "databases" / "mongodb" / "server" / "bin" / "mongod.exe"
PROJECT_MONGOD_DATA = ROOT / "databases" / "mongodb" / "data"
EXPECTED_MONGOD_PATH = PROJECT_MONGOD_BIN.resolve()


def _get_listener_pid(port):
    """Return PID listening on port, or None."""
    try:
        completed = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in completed.stdout.splitlines():
            line = line.strip()
            if not line or not line.upper().startswith("TCP"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            local_addr = parts[1]
            state = parts[3]
            pid_str = parts[4]
            if state != "LISTENING":
                continue
            if ":" not in local_addr:
                continue
            _, port_str = local_addr.rsplit(":", 1)
            try:
                if int(port_str) == port:
                    return int(pid_str)
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _get_process_executable(pid):
    """Return resolved Path to process executable, or None."""
    if pid is None:
        return None
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"Get-CimInstance Win32_Process -Filter 'ProcessId={pid}' | Select-Object -ExpandProperty ExecutablePath",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        raw = completed.stdout.strip()
        if not raw:
            return None
        path = Path(raw)
        if path.exists():
            return path.resolve()
    except Exception:
        pass
    return None


def _get_service_executable_path(service_name):
    """Return the executable path from a Windows service PathName, or None."""
    if not service_name:
        return None
    try:
        script = (
            "$svc = Get-CimInstance Win32_Service -Filter \"Name='{0}'\" "
            "-ErrorAction SilentlyContinue; "
            "if ($svc) { "
            "  $p = $svc.PathName.Trim(); "
            "  if ($p -match '^\"([^\"]+)\"') { $Matches[1] } "
            "  else { ($p -split ' ')[0] } "
            "} else { '' }"
        ).format(service_name.replace("'", "''"))
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        raw = completed.stdout.strip()
        if not raw:
            return None
        path = Path(raw)
        if path.exists():
            return path.resolve()
    except Exception:
        pass
    return None


def _get_service_status(service_name):
    """Return Windows service status string, or None if service not found."""
    if not service_name:
        return None
    try:
        script = (
            "$svc = Get-Service -Name '{0}' -ErrorAction SilentlyContinue; "
            "if ($svc) { $svc.Status } else { '' }"
        ).format(service_name.replace("'", "''"))
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        status = completed.stdout.strip()
        return status if status else None
    except Exception:
        return None


import tempfile

# Cache helper script path to avoid rewriting on every call
_HELPER_PS1_PATH = ROOT / "scripts" / "powershell" / "get_service_info.ps1"


def _get_service_info(service_name):
    """Return service ProcessId and resolved executable path, or None."""
    if not service_name:
        return None
    try:
        if not _HELPER_PS1_PATH.exists():
            return None
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", str(_HELPER_PS1_PATH),
                service_name,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        raw = completed.stdout.strip()
        if not raw or raw == "NOT_FOUND" or "|" not in raw:
            return None
        pid_str, path_str = raw.split("|", 1)
        path = Path(path_str)
        return {
            "ProcessId": int(pid_str),
            "ExecutablePath": path.resolve() if path.exists() else path,
        }
    except Exception:
        return None


def _is_project_owned(pid):
    """Check whether the listener PID belongs to the expected project-managed mongod.

    Ownership is determined by positive durable evidence in this order:
    1. Listener executable path matches the durable service MongoDBAutomation PathName.
    2. Listener PID matches the durable service MongoDBAutomation ProcessId.
    3. Listener executable path matches the current workspace's expected path.
    """
    if pid is None:
        return False

    actual = _get_process_executable(pid)

    try:
        service_info = _get_service_info("MongoDBAutomation")
        if service_info is not None:
            service_exe = service_info.get("ExecutablePath")
            if actual is not None and service_exe is not None and actual == service_exe:
                return True
            if pid == service_info.get("ProcessId"):
                return True
    except Exception:
        pass

    if actual is not None:
        try:
            return actual == EXPECTED_MONGOD_PATH
        except Exception:
            return False

    return False


def check():
    result = {
        "HOST": HOST,
        "PORT": str(PORT),
        "DATABASE": DB,
        "PROJECT_BINARIES_EXIST": "FALSE",
        "PROJECT_DATA_EXISTS": "FALSE",
        "TCP_OPEN": "FALSE",
        "MONGODB_AVAILABLE": "FALSE",
        "INSTANCE_STATE": "NO_INSTANCE",
        "ERROR": "None",
    }

    if PROJECT_MONGOD_BIN.exists():
        result["PROJECT_BINARIES_EXIST"] = "TRUE"

    if PROJECT_MONGOD_DATA.exists():
        result["PROJECT_DATA_EXISTS"] = "TRUE"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    tcp_result = sock.connect_ex((HOST, PORT))
    sock.close()

    if tcp_result != 0:
        result["ERROR"] = f"Port {PORT} is not listening"
        service_status = _get_service_status("MongoDBAutomation")
        if service_status is not None:
            result["INSTANCE_STATE"] = "INSTANCE_INSTALLED_BUT_STOPPED"
        elif result["PROJECT_BINARIES_EXIST"] == "TRUE":
            result["INSTANCE_STATE"] = "INSTANCE_INSTALLED_BUT_STOPPED"
        else:
            result["INSTANCE_STATE"] = "NO_INSTANCE"
        return result

    result["TCP_OPEN"] = "TRUE"

    listener_pid = _get_listener_pid(PORT)

    if not _is_project_owned(listener_pid):
        actual_path = _get_process_executable(listener_pid)
        actual_path_str = str(actual_path) if actual_path else "Unknown"
        result["ERROR"] = (
            f"Port {PORT} occupied by foreign process "
            f"(PID={listener_pid}, path={actual_path_str}). "
            f"Expected project-managed mongod: {EXPECTED_MONGOD_PATH}"
        )
        result["INSTANCE_STATE"] = "PORT_OCCUPIED_BY_NON_MONGODB"
        return result

    try:
        client = MongoClient(f"mongodb://{HOST}:{PORT}", serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        client.close()
        result["MONGODB_AVAILABLE"] = "TRUE"
    except PyMongoError as e:
        result["ERROR"] = str(e)
        if result["PROJECT_BINARIES_EXIST"] == "TRUE":
            result["INSTANCE_STATE"] = "INSTANCE_INSTALLED_BUT_STOPPED"
        else:
            result["INSTANCE_STATE"] = "NO_INSTANCE"
        return result

    result["INSTANCE_STATE"] = "INSTANCE_RUNNING_AND_USABLE"
    return result


if __name__ == "__main__":
    r = check()
    for k, v in r.items():
        print(f"{k}={v}")
