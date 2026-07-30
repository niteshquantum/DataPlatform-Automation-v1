"""
MSSQL Object Validator

Validates deployed database objects by querying SQL Server system catalog views.

Object discovery uses standard SQL Server catalogs:
  - sys.views               : views
  - sys.procedures          : stored procedures
  - sys.objects (type FN,IF,TF,FS,FT) : scalar and table-valued functions
  - sys.triggers            : DML triggers
  - sys.indexes             : indexes (excluding heaps index_id=0)

No events (MySQL-specific) and no materialized views (PostgreSQL-specific).

Connection uses pyodbc via config/windows/mssql.conf.
"""

import pyodbc

from config_loader import load_database_config


class MSSQLObjectValidator:

    def __init__(self):

        self.config = load_database_config("mssql")

        self.connection = None

    def connect(self):

        driver  = self.config.get("MSSQL_ODBC_DRIVER", "ODBC Driver 17 for SQL Server")
        host    = self.config["MSSQL_HOST"]
        port    = self.config["MSSQL_PORT"]
        db      = self.config["MSSQL_DB"]
        user    = self.config["MSSQL_USER"]
        pwd     = self.config.get("MSSQL_PASSWORD", "")

        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={db};"
            f"UID={user};"
            f"PWD={pwd};"
            f"TrustServerCertificate=yes;"
        )

        self.connection = pyodbc.connect(conn_str)

        print("Connected to MSSQL successfully.")

    def close(self):

        if self.connection:

            self.connection.close()

            self.connection = None

    def _fetch_names(self, query):

        cursor = self.connection.cursor()

        try:

            cursor.execute(query)

            return {
                str(row[0]).lower()
                for row in cursor.fetchall()
            }

        finally:

            cursor.close()

    def get_views(self):

        return self._fetch_names(
            """
            SELECT v.name
            FROM sys.views v
            JOIN sys.schemas s ON s.schema_id = v.schema_id
            WHERE v.is_ms_shipped = 0
            """
        )

    def get_functions(self):

        return self._fetch_names(
            """
            SELECT o.name
            FROM sys.objects o
            JOIN sys.schemas s ON s.schema_id = o.schema_id
            WHERE o.type IN ('FN', 'IF', 'TF', 'FS', 'FT')
              AND o.is_ms_shipped = 0
            """
        )

    def get_procedures(self):

        return self._fetch_names(
            """
            SELECT p.name
            FROM sys.procedures p
            JOIN sys.schemas s ON s.schema_id = p.schema_id
            WHERE p.is_ms_shipped = 0
            """
        )

    def get_triggers(self):

        return self._fetch_names(
            """
            SELECT t.name
            FROM sys.triggers t
            WHERE t.parent_class = 1
              AND t.is_ms_shipped = 0
            """
        )

    def get_indexes(self):

        return self._fetch_names(
            """
            SELECT i.name
            FROM sys.indexes i
            JOIN sys.tables tb ON tb.object_id = i.object_id
            WHERE i.index_id > 0
              AND tb.is_ms_shipped = 0
              AND i.name IS NOT NULL
            """
        )
