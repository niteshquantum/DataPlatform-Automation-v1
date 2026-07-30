from pathlib import Path

from config_loader import get_project_root
from template_loader import load_liquibase_template


class XMLGeneratorBase:

    def __init__(self, database, object_type):

        self.database = database
        self.object_type = object_type

        self.project_root = get_project_root()

        # Generated SQL files:
        #
        # objects/<database>/generated/<object_type>/
        #
        # Example:
        # objects/mysql/generated/views/
        self.sql_folder = (
            self.project_root
            / "objects"
            / database
            / "generated"
            / object_type
        )

        # Generated Liquibase XML files:
        #
        # liquibase/<database>/objects/generated/<object_type>/
        #
        # Example:
        # liquibase/mysql/objects/generated/views/
        self.xml_folder = (
            self.project_root
            / "liquibase"
            / database
            / "objects"
            / "generated"
            / object_type
        )

        self.xml_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        self.template = load_liquibase_template(
            database,
            object_type
        )

    def generate(self):

        if not self.sql_folder.exists():

            print(
                f"SQL folder not found, skipping: "
                f"{self.sql_folder}"
            )

            return

        sql_files = sorted(
            self.sql_folder.glob("*.sql")
        )

        if not sql_files:

            print(
                f"No SQL files found for: "
                f"{self.object_type}"
            )

            return

        for count, sql_file in enumerate(
            sql_files,
            start=1
        ):

            #
            # IMPORTANT:
            #
            # run_liquibase.bat uses:
            #
            # --search-path="%ROOT%"
            #
            # Therefore sqlFile path must be relative
            # to PROJECT_ROOT, not relative to XML file.
            #
            # Example:
            #
            # objects/mysql/generated/views/001_v_brands.sql
            #

            sql_path = (
                sql_file
                .relative_to(self.project_root)
                .as_posix()
            )

            xml_content = self.template.format(

                change_id=f"{self.object_type}-{count}",

                sql_file=sql_path,

                database=self.database,

                object_type=self.object_type
            )

            xml_file = (
                self.xml_folder
                / f"{sql_file.stem}.xml"
            )

            with open(
                xml_file,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(xml_content)

            print(
                f"Generated : {xml_file.name}"
            )