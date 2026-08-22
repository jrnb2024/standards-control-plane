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


def test_resolve_domain_matches_scp_enforcement_core_paths() -> None:
    # SCP's own enforcement core (the policy-check gate + its invocation lib)
    # must resolve to a domain so audit_changed governs changes to it instead
    # of falling to the vacuous governance fallback at confidence 0.
    # FUP-APPLIES-TO-ENFORCEMENT-CORE-COVERAGE-001. The reusable workflow
    # .github/workflows/policy-check.yml is the CI-side half of the TCB
    # (governed by GOV-008); the SCP-self exact wrapper is not mapped (see
    # the over-broadening guard below).
    for path in (
        "scripts/scp-policy-check",
        "lib/policy_check_invocation.sh",
        ".github/workflows/policy-check.yml",
    ):
        response = tools.resolve_domain_impl(
            tools.ResolveDomainRequest(changed_files=[path])
        )
        assert "governance" in response.domains, path
        assert response.confidence == 0.75, path


def test_resolve_domain_enforcement_core_globs_do_not_capture_adopter_scripts() -> None:
    # Over-broadening guard: the enforcement-core coverage is SCP-self exact
    # paths only, NOT a blanket scripts/**/lib/** — a representative adopter
    # deploy/helper script must NOT newly resolve to governance.
    deploy = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(changed_files=["scripts/deploy-staging.sh"])
    )
    assert "governance" not in deploy.domains

    helper = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(changed_files=["lib/some_adopter_helper.sh"])
    )
    assert "governance" not in helper.domains

    # The exact-path pattern must not spill onto the .lock sibling, which
    # VERSIONING.md treats as a distinct internal surface.
    lock = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(changed_files=["scripts/scp-policy-check.lock"])
    )
    assert "governance" not in lock.domains

    # Only the reusable workflow (policy-check.yml) is mapped, NOT the thin
    # caller wrapper (policy-check-wrapper.yml — the canonical adopter name)
    # nor any other .github/workflows file. Mapping the wrapper would surface
    # governance rules on every adopter's routine SHA-pin bump.
    for unmapped in (
        ".github/workflows/policy-check-wrapper.yml",
        ".github/workflows/ci.yml",
        # sibling of the mapped workflow, distinct final segment
        ".github/workflows/policy-check.yml.bak",
    ):
        response = tools.resolve_domain_impl(
            tools.ResolveDomainRequest(changed_files=[unmapped])
        )
        assert "governance" not in response.domains, unmapped

    # Backslash-normalised input still matches the mapped workflow (glob_matches
    # normalises separators), so a Windows-style path is not a silent miss.
    backslash = tools.resolve_domain_impl(
        tools.ResolveDomainRequest(
            changed_files=[".github\\workflows\\policy-check.yml"]
        )
    )
    assert "governance" in backslash.domains


def test_governance_fallback_surfaces_enforcement_core_on_resource_plane() -> None:
    # Two-plane lockstep: the resource plane (_applies_to_for_rule) must inherit
    # the enforcement-core paths for a governance rule with no explicit
    # applies_to, exactly as the tool plane (resolve_domain) does. Mirrors
    # test_architecture_fallback_surfaces_go_files.
    from standards_control_plane.applies_to import FALLBACK_APPLIES_TO_BY_DOMAIN
    from standards_control_plane.mcp_server.resources import _applies_to_for_rule

    gov_fallback = FALLBACK_APPLIES_TO_BY_DOMAIN["governance"]
    assert "scripts/scp-policy-check" in gov_fallback
    assert "lib/policy_check_invocation.sh" in gov_fallback
    assert ".github/workflows/policy-check.yml" in gov_fallback
    # exact SCP-self paths, NOT a blanket scripts/**/lib/**/.github/workflows/**
    # that would capture adopter deploy/helper scripts or wrapper workflows.
    assert "scripts/**" not in gov_fallback
    assert "lib/**" not in gov_fallback
    assert ".github/workflows/**" not in gov_fallback
    assert ".github/workflows/policy-check-wrapper.yml" not in gov_fallback

    resolved = _applies_to_for_rule({"rule_id": "GOV-002", "domain": "governance"})
    assert "scripts/scp-policy-check" in resolved
    assert "lib/policy_check_invocation.sh" in resolved
    assert ".github/workflows/policy-check.yml" in resolved


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
