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
    # SVC-004 (deploy recipe) must fire on the deploy scripts, not just services.yml.
    assert by_rule["SVC-004"]["domain"] == "service-lifecycle"
    assert "scripts/deploy-dev.sh" in by_rule["SVC-004"]["globs"]
    assert "scripts/deploy-staging.sh" in by_rule["SVC-004"]["globs"]


def test_architecture_fallback_surfaces_go_files() -> None:
    # R3.0: architecture rules must surface (advisory consult) on Go files, not
    # only .py/.ts — control-tower + mapp-pim are heavily Go. This gates the
    # *fallback* globs applied to architecture-domain rules that carry no
    # explicit applies_to (the real ARCH-001..005), so consult_rules /
    # audit_changed flag architecture rules when a Go file changes.
    from standards_control_plane.mcp_server.resources import (
        _FALLBACK_APPLIES_TO_BY_DOMAIN,
        _applies_to_for_rule,
    )

    arch_fallback = _FALLBACK_APPLIES_TO_BY_DOMAIN["architecture"]
    assert "src/**/*.go" in arch_fallback
    assert "packages/**/*.go" in arch_fallback
    # blanket **/*.go is intentionally NOT used (would match vendored/example Go).
    assert "**/*.go" not in arch_fallback

    # a real architecture rule with no explicit applies_to inherits the Go globs
    resolved = _applies_to_for_rule({"rule_id": "ARCH-005", "domain": "architecture"})
    assert "src/**/*.go" in resolved
    assert "packages/**/*.go" in resolved
