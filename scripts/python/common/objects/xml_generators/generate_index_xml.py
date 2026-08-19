import re
from xml.sax.saxutils import escape

from xml_generators.xml_generator_base import XMLGeneratorBase


def _mysql_sql_literal(value):
    """Return a value safe for a single-quoted SQL literal inside XML."""
    return escape(value.replace("'", "''"))


def _parse_mysql_index(sql_text, sql_file):
    """
    Extract MySQL index identity and indexed columns from CREATE INDEX SQL.

    Supports:
        CREATE INDEX idx ON table (column)
        CREATE INDEX idx ON table (column1, column2)

    The generated SQL is handled dynamically in the Liquibase template
    so TEXT/BLOB columns can receive an appropriate index prefix.
    """

    match = re.search(
        r"""
        CREATE\s+INDEX\s+
        (?P<index>[`"]?[^\s`"]+[`"]?)
        \s+ON\s+
        (?P<table>[`"]?[^\s(`"]+[`"]?)
        \s*\(
        (?P<columns>.*?)
        \)
        \s*;?
        """,
        sql_text,
        re.IGNORECASE | re.VERBOSE | re.DOTALL,
    )

    if not match:
        raise ValueError(
            f"Unable to determine MySQL index metadata: {sql_file}"
        )

    index_name = match.group("index").strip("`\"")
    table_name = match.group("table").strip("`\"")

    raw_columns = match.group("columns")

    columns = []

    for column in raw_columns.split(","):
        column = column.strip()

        # Remove optional backticks/quotes.
        column = column.strip("`\"")

        if not column:
            continue

        columns.append(column)

    if not columns:
        raise ValueError(
            f"Unable to determine MySQL index columns: {sql_file}"
        )

    return {
        "index_name": index_name,
        "table_name": table_name,
        "columns": columns,
    }


def generate_index_xml(database):

    generator = XMLGeneratorBase(
        database,
        "indexes"
    )

    sql_files = sorted(
        generator.sql_folder.glob("*.sql")
    )

    for change_id, sql_file in enumerate(sql_files, start=1):

        template_values = {
            "id": f"index-{change_id}",
            "sql_path": (
                sql_file
                .relative_to(generator.project_root)
                .as_posix()
            ),
        }

        # MySQL-specific handling only.
        # MSSQL/PostgreSQL/MongoDB remain unchanged.
        if database == "mysql":

            sql_text = sql_file.read_text(
                encoding="utf-8"
            )

            index_details = _parse_mysql_index(
                sql_text,
                sql_file
            )

            template_values.update(
                index_name_sql=_mysql_sql_literal(
                    index_details["index_name"]
                ),
                table_name_sql=_mysql_sql_literal(
                    index_details["table_name"]
                ),
                index_name_sql_identifier=escape(
                    index_details["index_name"]
                ),
                table_name_sql_identifier=escape(
                    index_details["table_name"]
                ),
                column_names_sql=", ".join(
                    _mysql_sql_literal(column)
                    for column in index_details["columns"]
                ),
                column_count=len(
                    index_details["columns"]
                ),
            )

        xml = generator.template.format(
            **template_values
        )

        xml_file = (
            generator.xml_folder
            / f"{sql_file.stem}.xml"
        )

        with open(
            xml_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(xml)

        print(
            f"Generated : {xml_file.name}"
        )