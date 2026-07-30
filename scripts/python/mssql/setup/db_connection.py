from pathlib import Path
import sys

import pyodbc

# =====================================
# PROJECT ROOT
# =====================================

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

# =====================================
# LOAD CONFIG
# =====================================

from scripts.python.common.config_loader import load_database_config

config = load_database_config("mssql")

# =====================================
# CONNECTION
# =====================================

def get_connection(database=None):
    """
    Returns a pyodbc connection to SQL Server.

    If database is None, the configured MSSQL_DB is used.
    """

    target_database = database or config["MSSQL_DB"]

    connection_string = (
        f"DRIVER={{{config['MSSQL_ODBC_DRIVER']}}};"
        f"SERVER={config['MSSQL_HOST']},{config['MSSQL_PORT']};"
        f"DATABASE={target_database};"
        f"UID={config['MSSQL_USER']};"
        f"PWD={config['MSSQL_PASSWORD']};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(connection_string)


# =====================================
# DATABASE
# =====================================

def get_cursor(database=None):
    """
    Returns (connection, cursor).
    """

    connection = get_connection(database)
    cursor = connection.cursor()

    return connection, cursor