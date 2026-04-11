"""JSON schema loading and validation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .resources import schemas_dir


def load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(name: str) -> dict[str, Any]:
    schema_path = schemas_dir() / name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    schema = load_json_file(schema_path)
    if not isinstance(schema, dict):
        raise TypeError(f"Schema must be an object: {schema_path}")
    return schema


def validate_with_schema(instance: Any, schema_name: str) -> None:
    schema = load_schema(schema_name)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    if errors:
        details = "; ".join(error.message for error in errors[:5])
        raise ValueError(f"{schema_name} validation failed: {details}")

