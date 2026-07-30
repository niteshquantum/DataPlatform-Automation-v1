import importlib


OBJECT_TYPE_MAP = {
    "views": "view",
    "functions": "function",
    "procedures": "procedure",
    "triggers": "trigger",
    "events": "event",
    "indexes": "index",
    # PostgreSQL-specific
    "materialized_views": "materialized_view",
    "extensions": "extension",
}


def normalize_object_type(object_type):

    return OBJECT_TYPE_MAP.get(
        object_type,
        object_type
    )


def load_template(database, object_type):

    object_type = normalize_object_type(
        object_type
    )

    module_name = (
        f"templates.{database}.{object_type}_template"
    )

    module = importlib.import_module(
        module_name
    )

    variable_name = (
        f"{object_type.upper()}_TEMPLATE"
    )

    return getattr(
        module,
        variable_name
    )


def load_liquibase_template(database, object_type):

    object_type = normalize_object_type(
        object_type
    )

    module_name = (
        f"templates.{database}."
        f"liquibase_{object_type}_template"
    )

    module = importlib.import_module(
        module_name
    )

    variable_name = (
        f"LIQUIBASE_{object_type.upper()}_TEMPLATE"
    )

    return getattr(
        module,
        variable_name
    )   