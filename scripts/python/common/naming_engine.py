#!/usr/bin/env python

"""
Generic Naming Engine

Provides configurable, reusable table and column name transformations:
- snake_case, camelCase, PascalCase, kebab-case, lowercase, UPPERCASE, preserve
- Configurable character replacements
- Explicit overrides
- Collision handling (fail / suffix)
"""

import re


# ============================================================
# STYLE TRANSFORMER
# ============================================================

def apply_naming_style(name: str, style: str) -> str:
    if not isinstance(name, str):
        raise TypeError("name must be a string")

    if style == "preserve":
        return name

    if style == "lowercase":
        return name.lower()

    if style == "UPPERCASE":
        return name.upper()

    s = name
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = re.sub(r"[-\s\.]+", "_", s)

    if style == "snake_case":
        return s.lower()

    if style == "kebab-case":
        return s.lower().replace("_", "-")

    if style == "camelCase":
        parts = s.split("_")
        if not parts:
            return ""
        result = parts[0].lower()
        for part in parts[1:]:
            result += part.capitalize()
        return result

    if style == "PascalCase":
        parts = s.split("_")
        result = ""
        for part in parts:
            result += part.capitalize()
        return result

    raise ValueError(f"Unsupported naming style: {style}")


# ============================================================
# CHARACTER REPLACEMENTS
# ============================================================

def apply_character_replacements(name: str, replacements: dict) -> str:
    if not isinstance(name, str):
        raise TypeError("name must be a string")

    result = name
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


# ============================================================
# GENERIC CLEANUP
# ============================================================

def cleanup_name(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError("name must be a string")

    result = name.strip()
    if not result:
        raise ValueError("Resulting name is empty after cleanup")

    result = re.sub(r"_{2,}", "_", result)
    result = result.strip("_")
    if not result:
        raise ValueError("Resulting name is empty after cleanup")

    return result


# ============================================================
# COLLISION HANDLING
# ============================================================

class CollisionError(Exception):
    pass


def resolve_collisions(
    names: list,
    strategy: str,
    separator: str = "_",
    start_index: int = 2,
) -> list:
    if not isinstance(names, list):
        raise TypeError("names must be a list")

    if strategy not in ("fail", "suffix"):
        raise ValueError(f"Unsupported collision strategy: {strategy}")

    result = []
    counter = {}

    for source_name, target_name in names:
        if target_name in counter:
            if strategy == "fail":
                sources = [s for s, t in names if t == target_name]
                raise CollisionError(
                    f"Collision detected: source names {sources} "
                    f"both map to target '{target_name}' "
                    f"(strategy: fail)"
                )
            if strategy == "suffix":
                count = counter[target_name]
                new_name = f"{target_name}{separator}{count}"
                counter[target_name] = count + 1
                counter[new_name] = start_index
                result.append((source_name, new_name))
                continue
        counter[target_name] = start_index
        result.append((source_name, target_name))

    return result


# ============================================================
# RESOLVE SINGLE NAME
# ============================================================

def resolve_name(
    source_name: str,
    style: str,
    replacements: dict,
    overrides: dict,
) -> str:
    if not isinstance(source_name, str):
        raise TypeError("source_name must be a string")

    if source_name in overrides:
        return overrides[source_name]

    lower_source = source_name.lower()
    for key, value in overrides.items():
        if key.lower() == lower_source:
            return value

    result = apply_character_replacements(source_name, replacements)
    result = apply_naming_style(result, style)
    result = cleanup_name(result)
    return result


# ============================================================
# BATCH RESOLVER
# ============================================================

def resolve_names(
    source_names: list,
    style: str,
    replacements: dict,
    overrides: dict,
    collision_strategy: str = "suffix",
    collision_separator: str = "_",
    collision_start_index: int = 2,
) -> list:
    if not isinstance(source_names, list):
        raise TypeError("source_names must be a list")

    mapped = []
    for name in source_names:
        target = resolve_name(name, style, replacements, overrides)
        mapped.append((name, target))

    return resolve_collisions(
        mapped,
        strategy=collision_strategy,
        separator=collision_separator,
        start_index=collision_start_index,
    )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "apply_naming_style",
    "apply_character_replacements",
    "cleanup_name",
    "resolve_collisions",
    "resolve_name",
    "resolve_names",
    "CollisionError",
]
