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

    for change_id, sql_file in enumerate(sql_files, start=1):

        template_values = {
            "id": f"index-{change_id}",
            "sql_path": (
                sql_file
                .relative_to(generator.project_root)
                .as_posix()
            ),
        }

        # MySQL generated indexes are recreated on every object-generation
        # run.  Supply the actual object identity so its Liquibase changeset
        # can reconcile an index that already exists without masking other
        # deployment errors.  Other database templates are deliberately
        # unchanged.
        if database == "mysql":
            index_match = re.search(
                r"CREATE\s+INDEX\s+([`\"]?[^\s`\"]+[`\"]?)\s+ON\s+([`\"]?[^\s(`\"]+[`\"]?)",
                sql_file.read_text(encoding="utf-8"),
                re.IGNORECASE,
            )

            if not index_match:
                raise ValueError(
                    f"Unable to determine MySQL index metadata: {sql_file}"
                )

            template_values.update(
                index_name=index_match.group(1).strip("`\""),
                table_name=index_match.group(2).strip("`\""),
            )

        xml = generator.template.format(**template_values)

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
