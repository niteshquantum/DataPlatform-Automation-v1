import re

from xml_generators.xml_generator_base import XMLGeneratorBase


def _mysql_index_columns(sql_text):
    match = re.search(
        r"CREATE\s+INDEX\s+(?P<index_name>`?[A-Za-z0-9_]+`?)\s+ON\s+(?P<table_name>`?[A-Za-z0-9_]+`?)\s*\((?P<columns>.+?)\)\s*;",
        sql_text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return None

    index_name = match.group("index_name").strip("`")
    table_name = match.group("table_name").strip("`")
    columns = [
        column.strip().strip("`\"'")
        for column in match.group("columns").split(",")
        if column.strip()
    ]

    if not columns:
        return None

    return {
        "index_name": index_name,
        "table_name": table_name,
        "column_xml": "\n".join(
            f'            <column name="{column}"/>'
            for column in columns
        ),
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

        if database == "mysql":
            sql_text = sql_file.read_text(encoding="utf-8")
            index_details = _mysql_index_columns(sql_text)

            if index_details is None:
                xml = generator.template.format(
                    id=f"index-{change_id}",
                    sql_path=(
                        sql_file
                        .relative_to(generator.project_root)
                        .as_posix()
                    ),
                    index_name="",
                    table_name="",
                    column_xml="",
                )
            else:
                xml = generator.template.format(
                    id=f"index-{change_id}",
                    sql_path=(
                        sql_file
                        .relative_to(generator.project_root)
                        .as_posix()
                    ),
                    index_name=index_details["index_name"],
                    table_name=index_details["table_name"],
                    column_xml=index_details["column_xml"],
                )
        else:
            xml = generator.template.format(
                id=f"index-{change_id}",
                sql_path=(
                    sql_file
                    .relative_to(generator.project_root)
                    .as_posix()
                ),
                index_name="",
                table_name="",
                column_xml="",
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

        print(f"Generated : {xml_file.name}")