from scripts.python.mssql.setup.db_connection import get_connection


def main():
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("""
        SELECT s.name, t.name, c.name, ty.name, c.max_length, c.is_nullable
        FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id
        JOIN sys.columns c ON c.object_id=t.object_id JOIN sys.types ty ON ty.user_type_id=c.user_type_id
        ORDER BY s.name, t.name, c.column_id
    """)
    for schema, table, column, data_type, length, nullable in cursor.fetchall():
        print(f"{schema}.{table}: {column} {data_type}({length}) nullable={bool(nullable)}")
    cursor.close(); conn.close()


if __name__ == '__main__':
    main()
