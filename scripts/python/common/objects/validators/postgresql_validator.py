"""
PostgreSQL Object Validator

Validates deployed database objects by querying the PostgreSQL system catalogs.

Object discovery uses standard PostgreSQL catalog views:
  - information_schema.views           : regular views
  - pg_matviews                        : materialized views (PostgreSQL-specific)
  - information_schema.routines        : functions and procedures
  - information_schema.triggers        : triggers
  - pg_extension                       : extensions (PostgreSQL-specific)
  - pg_indexes                         : indexes

Connection is loaded from:
  Windows : config/windows/postgresql.conf
  Ubuntu  : config/ubuntu/postgresql.conf
"""

import psycopg2

from config_loader import load_database_config


class PostgreSQLObjectValidator:

    def __init__(self):

        # Automatically loads OS-appropriate postgresql.conf
        self.config = load_database_config("postgresql")

        self.connection = None

    def connect(self):

        self.connection = psycopg2.connect(

            host=self.config["POSTGRESQL_HOST"],

            port=int(
                self.config["POSTGRESQL_PORT"]
            ),

            dbname=self.config["POSTGRESQL_DB"],

            user=self.config["POSTGRESQL_USER"],

            password=self.config.get(
                "POSTGRESQL_PASSWORD",
                ""
            )
        )

        print("Connected to PostgreSQL successfully.")

    def close(self):

        if self.connection:

            self.connection.close()

            self.connection = None

    def _fetch_names(
        self,
        query
    ):

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
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            """
        )

    def get_materialized_views(self):
        """PostgreSQL-specific: materialized views via pg_matviews."""

        return self._fetch_names(
            """
            SELECT matviewname
            FROM pg_matviews
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            """
        )

    def get_functions(self):

        return self._fetch_names(
            """
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_type = 'FUNCTION'
              AND routine_schema NOT IN ('pg_catalog', 'information_schema')
            """
        )

    def get_procedures(self):

        return self._fetch_names(
            """
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_type = 'PROCEDURE'
              AND routine_schema NOT IN ('pg_catalog', 'information_schema')
            """
        )

    def get_triggers(self):

        return self._fetch_names(
            """
            SELECT trigger_name
            FROM information_schema.triggers
            WHERE trigger_schema NOT IN ('pg_catalog', 'information_schema')
            """
        )

    def get_extensions(self):
        """PostgreSQL-specific: installed extensions via pg_extension."""

        return {
            name.replace("-", "_")
            for name in self._fetch_names(
                """
                SELECT extname
                FROM pg_extension
                """
            )
        }

    def get_indexes(self):

        return self._fetch_names(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            """
        )
