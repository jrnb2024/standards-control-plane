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
