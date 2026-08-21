#!/usr/bin/env python

"""
Focused tests for the generic naming engine.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest

from scripts.python.common.naming_engine import (
    apply_naming_style,
    apply_character_replacements,
    cleanup_name,
    resolve_collisions,
    resolve_name,
    resolve_names,
    CollisionError,
)
from scripts.python.common.column_mapper import (
    load_naming_config,
    load_mapping_config,
    map_table_name,
    map_columns,
)


# ============================================================
# STYLE TESTS
# ============================================================

@pytest.mark.parametrize("name,expected", [
    ("Customer ID", "customer_id"),
    ("CustomerID", "customer_id"),
    ("customerID", "customer_id"),
    ("CUSTOMER_ID", "customer_id"),
    ("customer-id", "customer_id"),
    ("Customer.Name", "customer_name"),
    ("Customer   Name", "customer_name"),
    (" Customer Name", "_customer_name"),
    ("123Customer", "123_customer"),
    ("Customer___ID", "customer___id"),
])
def test_snake_case(name, expected):
    assert apply_naming_style(name, "snake_case") == expected


@pytest.mark.parametrize("name,expected", [
    ("Customer ID", "customerId"),
    ("CustomerID", "customerId"),
    ("customerID", "customerId"),
    ("CUSTOMER_ID", "customerId"),
    ("customer-id", "customerId"),
    ("Customer.Name", "customerName"),
    ("Customer   Name", "customerName"),
    (" Customer Name", "CustomerName"),
    ("123Customer", "123Customer"),
    ("Customer___ID", "customerId"),
])
def test_camel_case(name, expected):
    assert apply_naming_style(name, "camelCase") == expected


@pytest.mark.parametrize("name,expected", [
    ("Customer ID", "CustomerId"),
    ("CustomerID", "CustomerId"),
    ("customerID", "CustomerId"),
    ("CUSTOMER_ID", "CustomerId"),
    ("customer-id", "CustomerId"),
    ("Customer.Name", "CustomerName"),
    ("Customer   Name", "CustomerName"),
    (" Customer Name", "CustomerName"),
    ("123Customer", "123Customer"),
    ("Customer___ID", "CustomerId"),
])
def test_pascal_case(name, expected):
    assert apply_naming_style(name, "PascalCase") == expected


@pytest.mark.parametrize("name,expected", [
    ("Customer ID", "customer-id"),
    ("CustomerID", "customer-id"),
    ("customerID", "customer-id"),
    ("CUSTOMER_ID", "customer-id"),
    ("customer-id", "customer-id"),
    ("Customer.Name", "customer-name"),
    ("Customer   Name", "customer-name"),
    (" Customer Name", "-customer-name"),
    ("123Customer", "123-customer"),
    ("Customer___ID", "customer---id"),
])
def test_kebab_case(name, expected):
    assert apply_naming_style(name, "kebab-case") == expected


@pytest.mark.parametrize("name,expected", [
    ("Customer ID", "customer id"),
    ("CustomerID", "customerid"),
    ("customerID", "customerid"),
    ("CUSTOMER_ID", "customer_id"),
    ("customer-id", "customer-id"),
    ("Customer.Name", "customer.name"),
    ("Customer   Name", "customer   name"),
    (" Customer Name", " customer name"),
    ("123Customer", "123customer"),
    ("Customer___ID", "customer___id"),
])
def test_lowercase(name, expected):
    assert apply_naming_style(name, "lowercase") == expected


@pytest.mark.parametrize("name,expected", [
    ("Customer ID", "CUSTOMER ID"),
    ("CustomerID", "CUSTOMERID"),
    ("customerID", "CUSTOMERID"),
    ("CUSTOMER_ID", "CUSTOMER_ID"),
    ("customer-id", "CUSTOMER-ID"),
    ("Customer.Name", "CUSTOMER.NAME"),
    ("Customer   Name", "CUSTOMER   NAME"),
    (" Customer Name", " CUSTOMER NAME"),
    ("123Customer", "123CUSTOMER"),
    ("Customer___ID", "CUSTOMER___ID"),
])
def test_uppercase(name, expected):
    assert apply_naming_style(name, "UPPERCASE") == expected


@pytest.mark.parametrize("name,expected", [
    ("Customer ID", "Customer ID"),
    ("CustomerID", "CustomerID"),
    ("customerID", "customerID"),
    ("CUSTOMER_ID", "CUSTOMER_ID"),
    ("customer-id", "customer-id"),
    ("Customer.Name", "Customer.Name"),
    ("Customer   Name", "Customer   Name"),
    (" Customer Name", " Customer Name"),
    ("123Customer", "123Customer"),
    ("Customer___ID", "Customer___ID"),
])
def test_preserve(name, expected):
    assert apply_naming_style(name, "preserve") == expected


def test_unsupported_style():
    with pytest.raises(ValueError):
        apply_naming_style("Customer ID", "unsupported")


# ============================================================
# CHARACTER REPLACEMENT TESTS
# ============================================================

def test_replace_space():
    assert apply_character_replacements("Customer Name", {" ": "_"}) == "Customer_Name"


def test_replace_hyphen():
    assert apply_character_replacements("Customer-Name", {"-": "_"}) == "Customer_Name"


def test_replace_dot():
    assert apply_character_replacements("Customer.Name", {".": "_"}) == "Customer_Name"


def test_replace_at():
    assert apply_character_replacements("Customer@ID", {"@": "_"}) == "Customer_ID"


def test_replace_hash():
    assert apply_character_replacements("Customer#ID", {"#": "_"}) == "Customer_ID"


def test_replace_star_delete():
    assert apply_character_replacements("Customer*Name", {"*": ""}) == "CustomerName"


def test_replace_multiple_chars():
    replacements = {" ": "_", "-": "_", ".": "_", "@": "_", "#": "_", "*": ""}
    assert apply_character_replacements("Customer-Name@ID*Test", replacements) == "Customer_Name_IDTest"


def test_replace_dollar_dynamic():
    assert apply_character_replacements("Price$USD", {"$": "_"}) == "Price_USD"


def test_replace_empty_dict():
    assert apply_character_replacements("CustomerID", {}) == "CustomerID"


# ============================================================
# OVERRIDE TESTS
# ============================================================

def test_explicit_override_wins():
    overrides = {"Customer ID": "customerId"}
    assert resolve_name("Customer ID", "snake_case", {" ": "_"}, overrides) == "customerId"


def test_override_wins_over_style():
    overrides = {"Customer-ID": "customerId"}
    assert resolve_name("Customer-ID", "snake_case", {"-": "_"}, overrides) == "customerId"


def test_override_wins_over_replacement():
    overrides = {"Customer Name": "customerName"}
    replacements = {" ": "_"}
    assert resolve_name("Customer Name", "snake_case", replacements, overrides) == "customerName"


def test_case_insensitive_override():
    overrides = {"customerid": "cust_id"}
    assert resolve_name("CUSTOMERID", "snake_case", {}, overrides) == "cust_id"


def test_no_override_applies_style():
    overrides = {"Other": "other"}
    assert resolve_name("Customer Name", "snake_case", {" ": "_"}, overrides) == "customer_name"


# ============================================================
# COLLISION TESTS
# ============================================================

def test_suffix_collision():
    names = ["Customer-ID", "Customer_ID", "Customer ID"]
    result = resolve_names(
        names,
        style="snake_case",
        replacements={" ": "_", "-": "_"},
        overrides={},
        collision_strategy="suffix",
        collision_separator="_",
        collision_start_index=2,
    )
    targets = [t for _, t in result]
    assert targets == ["customer_id", "customer_id_2", "customer_id_3"]


def test_fail_collision():
    names = ["Customer-ID", "Customer_ID"]
    with pytest.raises(CollisionError):
        resolve_names(
            names,
            style="snake_case",
            replacements={" ": "_", "-": "_"},
            overrides={},
            collision_strategy="fail",
            collision_separator="_",
            collision_start_index=2,
        )


def test_override_collision_suffix():
    names = ["A", "B"]
    overrides = {"A": "same", "B": "same"}
    result = resolve_names(
        names,
        style="snake_case",
        replacements={},
        overrides=overrides,
        collision_strategy="suffix",
        collision_separator="_",
        collision_start_index=2,
    )
    targets = [t for _, t in result]
    assert targets == ["same", "same_2"]


def test_override_collision_fail():
    names = ["A", "B"]
    overrides = {"A": "same", "B": "same"}
    with pytest.raises(CollisionError):
        resolve_names(
            names,
            style="snake_case",
            replacements={},
            overrides=overrides,
            collision_strategy="fail",
            collision_separator="_",
            collision_start_index=2,
        )


def test_no_collision():
    names = ["Customer", "Supplier"]
    result = resolve_names(
        names,
        style="snake_case",
        replacements={},
        overrides={},
        collision_strategy="suffix",
        collision_separator="_",
        collision_start_index=2,
    )
    targets = [t for _, t in result]
    assert targets == ["customer", "supplier"]


# ============================================================
# EDGE CASE TESTS
# ============================================================

def test_empty_input_allowed():
    assert apply_naming_style("", "snake_case") == ""


def test_cleanup_empty_result():
    with pytest.raises(ValueError):
        cleanup_name("___")


def test_cleanup_only_underscores():
    with pytest.raises(ValueError):
        cleanup_name("___")


def test_leading_digit():
    assert resolve_name("123Customer", "snake_case", {}, {}) == "123_customer"


def test_leading_trailing_whitespace():
    assert resolve_name("  Customer Name  ", "snake_case", {" ": "_"}, {}) == "customer_name"


def test_repeated_separators():
    assert resolve_name("Customer   Name", "snake_case", {" ": "_"}, {}) == "customer_name"


def test_special_chars_with_replacements():
    assert resolve_name("Customer@ID", "snake_case", {"@": "_"}, {}) == "customer_id"
    assert resolve_name("Customer#ID", "snake_case", {"#": "_"}, {}) == "customer_id"
    assert resolve_name("Customer*Name", "snake_case", {"*": ""}, {}) == "customer_name"


def test_invalid_strategy():
    with pytest.raises(ValueError):
        resolve_collisions([], strategy="invalid")


# ============================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================

def test_engine_disabled_by_default():
    config = load_naming_config()
    assert config.get("settings", {}).get("enable_naming_engine", False) is False


def test_existing_column_mapping_behavior_preserved():
    config = load_mapping_config()
    config["settings"]["enable_mapping"] = True

    table = map_table_name("Customer Records", config)
    assert table == "customers"

    columns = map_columns(
        ["CustomerID", "FirstName", "LastName"],
        config
    )
    assert columns == ["customer_id", "first_name", "last_name"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
