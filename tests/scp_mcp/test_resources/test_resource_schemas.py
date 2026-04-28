from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from referencing import Registry, Resource

from .conftest import read_server_resource


def _schema_registry() -> Registry:
    registry = Registry()
    schema_root = Path("schemas/scp_mcp")
    for path in schema_root.glob("*.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        registry = registry.with_resource(
            f"schemas/scp_mcp/{path.name}",
            Resource.from_contents(contents),
        )
    return registry


def _validator(name: str) -> jsonschema.Draft202012Validator:
    schema = json.loads((Path("schemas/scp_mcp") / name).read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema, registry=_schema_registry())


def test_resource_payloads_validate_against_published_schemas(resource_server) -> None:
    schema_by_uri = {
        "scp://rules/registry": "rules-registry.schema.json",
        "scp://rules/domain-map": "domain-map.schema.json",
        "scp://decisions": "decisions.schema.json",
        "scp://findings/open": "findings-open.schema.json",
        "scp://waivers": "waivers.schema.json",
        "scp://status": "status.schema.json",
        "scp://security/signing-keys": "signing-keys.schema.json",
        "scp://rule/GOV-001": "rule-card.schema.json",
        "scp://waiver/W-001": "waiver.schema.json",
        "scp://finding/F-OPEN-001": "finding.schema.json",
        "scp://decision/D-1000": "decision.schema.json",
    }

    for uri, schema_name in schema_by_uri.items():
        payload = read_server_resource(resource_server, uri)
        _validator(schema_name).validate(payload)
