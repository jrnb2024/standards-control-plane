from __future__ import annotations


def test_domain_map_groups_globs_by_domain_and_rule(resource_catalog) -> None:
    payload = resource_catalog.read_static("scp://rules/domain-map")
    domain_map = payload["domain_map"]

    assert payload["schema_version"] == "1.0.0"
    assert payload["key_id"] == "scp-mcp-2026-04"
    assert domain_map["by_glob"]["docs/**/*.md"]["domains"] == ["governance"]
    assert domain_map["by_glob"]["docs/**/*.md"]["rule_ids"] == ["GOV-001"]
    assert domain_map["by_glob"]["src/**/*.py"]["domains"] == ["architecture"]
    assert domain_map["by_glob"]["src/**/*.py"]["rule_ids"] == ["ARCH-001"]


def test_domain_map_keeps_per_rule_isolation(resource_catalog) -> None:
    payload = resource_catalog.read_static("scp://rules/domain-map")
    by_rule = payload["domain_map"]["by_rule"]

    assert by_rule["GOV-001"] == {
        "domain": "governance",
        "globs": ["docs/**/*.md", "docs/DECISIONS.md"],
    }
    assert by_rule["ARCH-001"] == {
        "domain": "architecture",
        "globs": ["src/**/*.py"],
    }
    assert by_rule["SVC-001"] == {
        "domain": "service-lifecycle",
        "globs": ["services.yml", "**/services.yml"],
    }
