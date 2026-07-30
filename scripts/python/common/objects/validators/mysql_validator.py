import mysql.connector

from config_loader import load_database_config


class MySQLObjectValidator:

    def __init__(self):

        # Automatically loads:
        #
        # Windows:
        # config/windows/mysql.conf
        #
        # Ubuntu/Linux:
        # config/ubuntu/mysql.conf
        #
        self.config = load_database_config("mysql")

        self.connection = None

    def connect(self):

        self.connection = mysql.connector.connect(

            host=self.config["MYSQL_HOST"],

            port=int(
                self.config["MYSQL_PORT"]
            ),

            database=self.config["MYSQL_DB"],

            user=self.config["MYSQL_USER"],

            password=self.config.get(
                "MYSQL_PASSWORD",
                ""
            )
        )

        print("Connected to MySQL successfully.")

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
            SELECT TABLE_NAME
            FROM information_schema.VIEWS
            WHERE TABLE_SCHEMA = DATABASE()
            """
        )

    def get_functions(self):

        return self._fetch_names(
            """
            SELECT ROUTINE_NAME
            FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = DATABASE()
              AND ROUTINE_TYPE = 'FUNCTION'
            """
        )

    def get_procedures(self):

        return self._fetch_names(
            """
            SELECT ROUTINE_NAME
            FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = DATABASE()
              AND ROUTINE_TYPE = 'PROCEDURE'
            """
        )

    def get_triggers(self):

        return self._fetch_names(
            """
            SELECT TRIGGER_NAME
            FROM information_schema.TRIGGERS
            WHERE TRIGGER_SCHEMA = DATABASE()
            """
        )

    def get_events(self):

        return self._fetch_names(
            """
            SELECT EVENT_NAME
            FROM information_schema.EVENTS
            WHERE EVENT_SCHEMA = DATABASE()
            """
        )

    def get_indexes(self):

        return self._fetch_names(
            """
            SELECT DISTINCT INDEX_NAME
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND INDEX_NAME <> 'PRIMARY'
            """
        )