from config_loader import get_project_root
from template_loader import load_liquibase_template
from database_capabilities import get_supported_objects


def generate_custom_xml(database):

    root = get_project_root()

    custom_root = (
        root
        / "objects"
        / database
        / "custom"
    )

    print()
    print("----------------------------------------")
    print(f"Scanning Custom Objects : {database}")
    print("----------------------------------------")

    # Custom folder optional hai.
    if not custom_root.exists():

        print(
            "Custom objects folder not found. "
            "Skipping custom objects."
        )

        return

    generated_count = 0

    for object_type in get_supported_objects(database):

        sql_folder = (
            custom_root
            / object_type
        )

        # Example:
        # MySQL supports events,
        # PostgreSQL may support materialized_views.
        # Folder nahi hai to simply skip.
        if not sql_folder.exists():

            continue

        sql_files = sorted(
            sql_folder.glob("*.sql")
        )

        if not sql_files:

            continue

        template = load_liquibase_template(
            database,
            object_type
        )

        xml_folder = (
            root
            / "liquibase"
            / database
            / "objects"
            / "custom"
            / object_type
        )

        xml_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        for sql_file in sql_files:

            # Example:
            #
            # objects/mysql/custom/views/
            # 001_v_high_value_customers.sql
            #
            # run_liquibase already uses PROJECT_ROOT
            # as search path.
            sql_path = (
                sql_file
                .relative_to(root)
                .as_posix()
            )

            # Stable unique Liquibase ID.
            #
            # Filename-based ID means rerun par
            # same object same changeset identify hoga.
            change_id = (
                f"custom-"
                f"{object_type}-"
                f"{sql_file.stem}"
            )

            xml_content = template.format(
                id=change_id,
                sql_path=sql_path
            )

            xml_file = (
                xml_folder
                / f"{sql_file.stem}.xml"
            )

            xml_file.write_text(
                xml_content,
                encoding="utf-8"
            )

            print(
                f"Generated Custom XML : "
                f"{object_type}/"
                f"{xml_file.name}"
            )

            generated_count += 1

    if generated_count == 0:

        print(
            "No custom SQL objects found. "
            "Skipping custom Liquibase generation."
        )

    else:

        print(
            f"Custom Liquibase XML Generated : "
            f"{generated_count}"
        )

    print("----------------------------------------")