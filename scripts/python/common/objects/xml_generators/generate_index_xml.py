import re

from xml_generators.xml_generator_base import XMLGeneratorBase


def generate_index_xml(database):

    generator = XMLGeneratorBase(
        database,
        "indexes"
    )

    sql_files = sorted(
        generator.sql_folder.glob("*.sql")
    )

    for change_id, sql_file in enumerate(
        sql_files,
        start=1
    ):

        with open(
            sql_file,
            "r",
            encoding="utf-8"
        ) as file:
            sql = file.read()

        match = re.search(
            r"CREATE\s+INDEX\s+([`\"\w]+)\s+ON\s+([`\"\w]+)",
            sql,
            re.IGNORECASE
        )

        if not match:
            raise ValueError(
                f"Unable to determine index name/table name "
                f"from SQL file: {sql_file}"
            )

        index_name = match.group(1).strip("`\"")
        table_name = match.group(2).strip("`\"")

        xml = generator.template.format(
            id=f"index-{change_id}",
            sql_path=(
                sql_file
                .relative_to(generator.project_root)
                .as_posix()
            ),
            index_name=index_name,
            table_name=table_name
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