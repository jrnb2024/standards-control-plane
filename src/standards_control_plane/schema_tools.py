"""JSON schema loading and validation helpers."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from .resources import schemas_dir


def load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_schema_file(path: Path) -> dict[str, Any]:
    schema = load_json_file(path)
    if not isinstance(schema, dict):
        raise TypeError(f"Schema must be an object: {path}")
    if "$id" not in schema:
        schema = {"$id": path.as_uri(), **schema}
    return schema


def load_schema(name: str) -> dict[str, Any]:
    schema_path = schemas_dir() / name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    return _load_schema_file(schema_path)


@lru_cache(maxsize=1)
def _schema_registry() -> Registry:
    registry = Registry()
    for schema_path in sorted(schemas_dir().glob("*.json")):
        schema = _load_schema_file(schema_path)
        registry = registry.with_resource(
            schema_path.as_uri(),
            DRAFT202012.create_resource(schema),
        )
    return registry


def validate_with_schema(instance: Any, schema_name: str) -> None:
    schema = load_schema(schema_name)
    validator = Draft202012Validator(
        schema,
        registry=_schema_registry(),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    if errors:
        details = "; ".join(error.message for error in errors[:5])
        raise ValueError(f"{schema_name} validation failed: {details}")
