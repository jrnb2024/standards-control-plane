from __future__ import annotations

from standards_control_plane.mcp_server import tools


def test_resolve_domain_returns_exact_match_with_full_confidence() -> None:
    response = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(
            changed_files=["standards/architecture/rules/ARCH-001-service-boundaries.md"]
        )
    )

    assert response.domains == ["architecture"]
    assert response.confidence == 1.0


def test_resolve_domain_returns_fuzzy_frontend_domains() -> None:
    response = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(changed_files=["frontend/app/orders/page.tsx"])
    )

    assert {"architecture", "design", "product", "ux"}.issubset(set(response.domains))
    assert 0.0 < response.confidence < 1.0


def test_resolve_domain_matches_estate_go_service_paths() -> None:
    # Recommender-shaped path: Go source under services/<name>/.
    response = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(changed_files=["services/search/index.go"])
    )

    assert "architecture" in response.domains
    assert response.confidence > 0.0


def test_resolve_domain_matches_estate_python_service_paths() -> None:
    # mapp-pim-shaped path: Python source under services/<name>/.
    response = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(changed_files=["services/enrichment/context_rules.py"])
    )

    assert "architecture" in response.domains
    assert response.confidence > 0.0


def test_resolve_domain_matches_kg_studio_src_paths() -> None:
    response = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(changed_files=["src/lib/rules/revision.ts"])
    )

    assert "architecture" in response.domains
    assert response.confidence > 0.0


def test_resolve_domain_glob_matches_rank_between_fuzzy_and_exact() -> None:
    # A glob-tier match (no exact rule-document hit) must land above the
    # fuzzy heuristics but below an exact match.
    glob_only = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(changed_files=["services/enrichment/context_rules.py"])
    )

    assert glob_only.confidence == 0.75


def test_resolve_domain_demotes_exact_confidence_when_mixed_with_lower_tiers() -> None:
    exact_plus_glob = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(
            changed_files=[
                "standards/architecture/rules/ARCH-001-service-boundaries.md",
                "services/enrichment/context_rules.py",
            ]
        )
    )
    exact_plus_fuzzy = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(
            changed_files=[
                "standards/architecture/rules/ARCH-001-service-boundaries.md",
                "backend/api/orders_api_view.rb",
            ]
        )
    )

    assert exact_plus_glob.confidence == 0.8
    assert exact_plus_fuzzy.confidence == 0.8
