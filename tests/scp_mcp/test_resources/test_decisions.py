from __future__ import annotations


def test_decisions_resource_parses_markdown_table(resource_catalog) -> None:
    payload = resource_catalog.read_static("scp://decisions")

    assert payload["schema_version"] == "1.0.0"
    assert [decision["decision_id"] for decision in payload["decisions"]] == ["D-024", "D-028"]
    assert payload["decisions"][0]["decision"] == "Use MCP"
    assert payload["decisions"][1]["rationale"] == "Design parity"
