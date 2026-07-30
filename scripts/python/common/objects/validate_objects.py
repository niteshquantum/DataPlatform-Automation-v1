import sys
import json
from pathlib import Path


# ============================================================
# PYTHON PATH
# ============================================================

COMMON_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(COMMON_DIR)
)


from config_loader import get_project_root
from database_capabilities import supports_object


# ============================================================
# OBJECT NAME
# ============================================================

def get_object_name(sql_file):

    """
    Convert:

    001_v_brands.sql
        ->
    v_brands

    001_fn_active_brand_count.sql
        ->
    fn_active_brand_count
    """

    name = sql_file.stem

    parts = name.split("_", 1)

    if (
        len(parts) == 2
        and parts[0].isdigit()
    ):
        name = parts[1]

    return name.lower()


# ============================================================
# EXPECTED OBJECTS
# ============================================================

def get_expected_objects(
    root,
    database,
    object_type
):

    expected = {
        "generated": set(),
        "custom": set()
    }

    # Both layers are optional.
    sources = [
        "generated",
        "custom"
    ]

    for source in sources:

        folder = (
            root
            / "objects"
            / database
            / source
            / object_type
        )

        if not folder.exists():
            continue

        for sql_file in sorted(
            folder.glob("*.sql")
        ):

            object_name = get_object_name(
                sql_file
            )

            expected[source].add(
                object_name
            )

    return expected


# ============================================================
# VALIDATE OBJECT TYPE
# ============================================================

def validate_type(
    object_type,
    expected,
    actual
):

    generated = expected["generated"]
    custom = expected["custom"]

    all_expected = (
        generated
        | custom
    )

    missing_generated = (
        generated
        - actual
    )

    missing_custom = (
        custom
        - actual
    )

    missing = (
        all_expected
        - actual
    )

    print()

    print(
        f"{object_type.upper()}:"
    )

    print(
        f"  Generated : "
        f"{len(generated) - len(missing_generated)}"
        f"/{len(generated)}"
    )

    print(
        f"  Custom    : "
        f"{len(custom) - len(missing_custom)}"
        f"/{len(custom)}"
    )

    print(
        f"  Total     : "
        f"{len(all_expected) - len(missing)}"
        f"/{len(all_expected)}"
    )

    if missing:

        print("  STATUS    : FAIL")

        for name in sorted(missing):

            source = (
                "CUSTOM"
                if name in custom
                else "GENERATED"
            )

            print(
                f"  MISSING   : "
                f"{name} "
                f"[{source}]"
            )

        return False

    print(
        "  STATUS    : PASS"
    )

    return True


# ============================================================
# MAIN VALIDATION
# ============================================================

def validate_objects(database):

    database = database.lower()

    root = get_project_root()

    # --------------------------------------------------------
    # DATABASE VALIDATOR
    # --------------------------------------------------------

    if database == "mysql":

        from validators.mysql_validator import (
            MySQLObjectValidator
        )

        validator = (
            MySQLObjectValidator()
        )

    elif database == "postgresql":

        from validators.postgresql_validator import (
            PostgreSQLObjectValidator
        )

        validator = (
            PostgreSQLObjectValidator()
        )

    elif database == "mssql":

        from validators.mssql_validator import (
            MSSQLObjectValidator
        )

        validator = (
            MSSQLObjectValidator()
        )

    else:

        raise ValueError(
            f"No validator implemented for: "
            f"{database}"
        )

    print()

    print(
        "====================================="
    )

    print(
        "DATABASE OBJECT VALIDATION"
    )

    print(
        "====================================="
    )

    print(
        f"Database : {database}"
    )

    results = {}

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    try:

        validator.connect()

        # --------------------------------------------------------
        # Build getter map dynamically.
        # Each object_type maps to a validator method name.
        # If the validator does not have that method (e.g., MySQL
        # has no get_materialized_views), the type is skipped.
        # This means no branching per database is needed here.
        # --------------------------------------------------------

        OBJECT_TYPE_GETTER = {
            "views":              "get_views",
            "materialized_views": "get_materialized_views",
            "functions":          "get_functions",
            "procedures":         "get_procedures",
            "triggers":           "get_triggers",
            "events":             "get_events",
            "indexes":            "get_indexes",
            "extensions":         "get_extensions",
        }

        getters = {
            object_type: getattr(validator, method_name)
            for object_type, method_name in OBJECT_TYPE_GETTER.items()
            if hasattr(validator, method_name)
        }

        for object_type, getter in getters.items():

            if not supports_object(
                database,
                object_type
            ):
                continue

            expected = (
                get_expected_objects(
                    root,
                    database,
                    object_type
                )
            )

            actual = getter()

            generated = (
                expected["generated"]
            )

            custom = (
                expected["custom"]
            )

            all_expected = (
                generated
                | custom
            )

            missing = sorted(
                all_expected
                - actual
            )

            passed = (
                validate_type(
                    object_type,
                    expected,
                    actual
                )
            )

            results[object_type] = {

                "generated": {
                    "expected":
                        len(generated),

                    "found":
                        len(
                            generated
                            & actual
                        ),

                    "missing":
                        sorted(
                            generated
                            - actual
                        )
                },

                "custom": {
                    "expected":
                        len(custom),

                    "found":
                        len(
                            custom
                            & actual
                        ),

                    "missing":
                        sorted(
                            custom
                            - actual
                        )
                },

                "total": {
                    "expected":
                        len(all_expected),

                    "found":
                        len(
                            all_expected
                            & actual
                        ),

                    "missing":
                        missing
                },

                "status": (
                    "PASS"
                    if passed
                    else "FAIL"
                )
            }

    finally:

        validator.close()

    # ========================================================
    # REPORT
    # ========================================================

    report = (
        root
        / "metadata"
        / database
        / "object_validation_report.json"
    )

    report.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        report,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4
        )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    failed = [

        object_type

        for object_type, result
        in results.items()

        if result["status"]
        == "FAIL"
    ]

    print()

    print(
        "====================================="
    )

    if failed:

        print(
            "OBJECT VALIDATION FAILED"
        )

        print(
            "Failed types: "
            + ", ".join(failed)
        )

        print(
            f"Report : {report}"
        )

        raise RuntimeError(
            "Database object "
            "validation failed."
        )

    print(
        "ALL DATABASE OBJECTS VALIDATED"
    )

    print(
        f"Report : {report}"
    )

    print(
        "====================================="
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage: "
            "validate_objects.py "
            "<database>"
        )

        sys.exit(1)

    validate_objects(
        sys.argv[1]
    )