from __future__ import annotations

import time

from standards_control_plane.applies_to import applies_to_for_rule, glob_matches


def test_glob_matches_star_star_spans_zero_or_more_segments() -> None:
    assert glob_matches("services/enrichment/pipeline.py", "services/**/*.py")
    assert glob_matches("services/pipeline.py", "services/**/*.py")
    assert not glob_matches("service/pipeline.py", "services/**/*.py")
    assert glob_matches("style.css", "**/*.css")
    assert glob_matches("frontend/app/style.css", "**/*.css")


def test_glob_matches_single_star_never_crosses_segments() -> None:
    assert glob_matches("docker-compose.staging.yml", "docker-compose*.yml")
    assert not glob_matches("infra/docker-compose.yml", "docker-compose*.yml")
    assert glob_matches("services.yml", "**/services.yml")
    assert glob_matches("nested/dir/services.yml", "**/services.yml")


def test_glob_matches_is_polynomial_on_adversarial_patterns() -> None:
    # Multiple ** segments against a deep path must not fan out exponentially
    # (resolve_domain matches every changed file against every rule glob).
    path = "/".join(["segment"] * 60)
    pattern = "/".join(["**"] * 8 + ["*.py"])

    started = time.monotonic()
    result = glob_matches(path, pattern)
    elapsed = time.monotonic() - started

    assert result is False
    assert elapsed < 0.5


def test_applies_to_for_rule_declared_list_wins_over_fallbacks() -> None:
    assert applies_to_for_rule("ARCH-006", "architecture", declared=["custom/**"]) == ["custom/**"]
    # rule-specific fallback REPLACES the domain fallback
    assert "services.yml" in applies_to_for_rule("ARCH-006", "architecture")
    # domain fallback applies when no rule-specific entry exists
    assert "services/**/*.py" in applies_to_for_rule("ARCH-001", "architecture")
    assert applies_to_for_rule("XX-999", "unknown-domain") == []
