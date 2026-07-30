import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import load_database_config
from scripts.python.mssql.setup.db_connection import get_connection


def _powershell(script, timeout=10):
    try:
        result = subprocess.run(
            ["powershell", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as exc:
        return -1, "", str(exc)


def _get_service_image_path(service_name):
    try:
        result = subprocess.run(
            ["sc.exe", "qc", service_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        for line in result.stdout.splitlines():
            if "BINARY_PATH_NAME" in line:
                return line.split(":", 1)[1].strip()
        return None
    except Exception:
        return None


def _find_instance_id(instance):
    if instance == "MSSQLSERVER":
        return "MSSQLSERVER"

    ps_script = (
        "Get-ChildItem 'HKLM:\\SOFTWARE\\Microsoft\\Microsoft SQL Server' | "
        "ForEach-Object { "
        "  $id = $_.PSChildName; "
        "  $setup = Get-ItemProperty ($_.PSPath + '\\Setup') -ErrorAction SilentlyContinue; "
        f"  if ($setup -and $setup.InstanceName -eq '{instance}') {{ Write-Host $id }} "
        "}"
    )
    rc, out, _ = _powershell(ps_script)
    if rc == 0 and out:
        return out.splitlines()[0].strip()

    try:
        result = subprocess.run(
            [
                "reg", "query",
                r"HKLM\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL",
                "/v", instance,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.strip().startswith(instance + "    "):
                    parts = line.strip().split("    ", 2)
                    if len(parts) >= 3:
                        return parts[2].strip()
    except Exception:
        pass

    return None


def _get_registry_image_path(instance_id):
    reg_path = (
        f"HKLM\\SOFTWARE\\Microsoft\\Microsoft SQL Server\\{instance_id}\\Setup"
    )

    rc, out, _ = _powershell(
        f"Get-ItemProperty '{reg_path}' -ErrorAction SilentlyContinue "
        "| Select-Object -ExpandProperty ImagePath"
    )
    if rc == 0 and out:
        return out

    try:
        result = subprocess.run(
            ["reg", "query", reg_path, "/v", "ImagePath"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "ImagePath" in line and "REG_SZ" in line:
                    parts = line.strip().split("REG_SZ")
                    if len(parts) >= 2:
                        return parts[1].strip()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["reg", "query", reg_path, "/v", "SQLBinRoot"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "SQLBinRoot" in line and "REG_SZ" in line:
                    parts = line.strip().split("REG_SZ")
                    if len(parts) >= 2:
                        return str(Path(parts[1].strip()) / "sqlservr.exe")
    except Exception:
        pass

    return None


def check_instance():
    config = load_database_config("mssql")

    host = config["MSSQL_HOST"]
    port = int(config["MSSQL_PORT"])
    instance = config.get("MSSQL_INSTANCE", "MSSQLSERVER")

    print("=" * 60)
    print("CHECKING MSSQL INSTANCE")
    print("=" * 60)
    print(f"Host     : {host}")
    print(f"Port     : {port}")
    print(f"Instance : {instance}")
    print()

    service_name = (
        "MSSQLSERVER"
        if instance == "MSSQLSERVER"
        else f"MSSQL${instance}"
    )

    service_status = None
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Get-Service -Name '{service_name}' -ErrorAction SilentlyContinue "
             "| Select-Object -ExpandProperty Status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        service_status = result.stdout.strip()

        if result.returncode != 0 or not service_status:
            print(f"Service not found : {service_name}")
            print()
            print("INSTANCE_STATE=NO_INSTANCE")
            return "NO_INSTANCE"

        print(f"Service status : {service_status}")

    except Exception as e:
        print(f"Service check failed : {e}")
        print()
        print("INSTANCE_STATE=NO_INSTANCE")
        return "NO_INSTANCE"

    if service_status != "Running":
        print(f"Service status : {service_status}")
        print()
        print("INSTANCE_STATE=INSTANCE_INSTALLED_BUT_STOPPED")
        return "INSTANCE_INSTALLED_BUT_STOPPED"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((host, port))
    sock.close()

    if result != 0:
        print(f"Port not listening : {host}:{port}")
        print()
        print("INSTANCE_STATE=NO_INSTANCE")
        return "NO_INSTANCE"

    print(f"Port listening     : {host}:{port}")
    print()

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        print(f"Version : {version.splitlines()[0]}")
        print()
        print("INSTANCE_STATE=INSTANCE_RUNNING_AND_USABLE")
        return "INSTANCE_RUNNING_AND_USABLE"
    except Exception as e:
        print(f"Connection failed : {e}")
        print()
        print("INSTANCE_STATE=PORT_OCCUPIED_BY_NON_MSSQL")
        return "PORT_OCCUPIED_BY_NON_MSSQL"


if __name__ == "__main__":
    try:
        state = check_instance()
        sys.exit(0 if state == "INSTANCE_RUNNING_AND_USABLE" else 1)
    except Exception as e:
        print(f"\nERROR : {e}")
        sys.exit(1)
