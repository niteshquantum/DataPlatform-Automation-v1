from xml_generators.xml_generator_base import XMLGeneratorBase


def generate_function_xml(database):

    generator = XMLGeneratorBase(
        database,
        "functions"
    )

    sql_files = sorted(
        generator.sql_folder.glob("*.sql")
    )

    for change_id, sql_file in enumerate(sql_files, start=1):

        xml = generator.template.format(

            id=f"function-{change_id}",

            sql_path=(
                        sql_file
                        .relative_to(generator.project_root)
                        .as_posix()
                    )

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