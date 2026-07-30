from scripts.python.mssql.setup.db_connection import get_connection


def main():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DB_NAME(), CONVERT(varchar(128), DATABASEPROPERTYEX(DB_NAME(), 'Version')),
               compatibility_level, recovery_model_desc, collation_name
        FROM sys.databases WHERE name = DB_NAME()
    """)
    database, version, compatibility, recovery, collation = cursor.fetchone()
    print(f"Database Name: {database}\nVersion: {version}\nCompatibility Level: {compatibility}\nRecovery Model: {recovery}\nCollation: {collation}")
    cursor.execute("SELECT name, type_desc, size * 8.0 / 1024 AS size_mb FROM sys.database_files ORDER BY type_desc, name")
    for name, file_type, size_mb in cursor.fetchall():
        print(f"{file_type}: {name} ({size_mb:.2f} MB)")
    cursor.execute("SELECT name FROM sys.filegroups ORDER BY name")
    print("Filegroups: " + ", ".join(row[0] for row in cursor.fetchall()))
    cursor.close(); conn.close()


if __name__ == '__main__':
    main()
