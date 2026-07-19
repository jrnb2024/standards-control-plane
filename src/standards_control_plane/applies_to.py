"""Shared applies-to glob mappings and matching for rule relevance.

Single home for the per-rule / per-domain applies_to fallbacks so the MCP
resource plane (committed-state domain map) and the MCP tool plane
(resolve_domain path matching) stay in lockstep. The glob vocabulary is
estate-wide: patterns describe path shapes in ANY adopter repo (mapp-pim,
Recommender, kg-studio, control-tower, SCP itself), not just this repo's
own tree.
"""

from __future__ import annotations

from fnmatch import fnmatchcase

FALLBACK_APPLIES_TO_BY_RULE_ID: dict[str, tuple[str, ...]] = {
    "SVC-001": ("services.yml", "**/services.yml"),
    "SVC-002": ("services.yml", "**/services.yml"),
    "SVC-003": ("services.yml", "**/services.yml"),
    # ARCH-006 ontology-canonical-consumption (enforced via SCP-R-013). Relevance
    # covers the ontology_contract declaration surface (services.yml) plus the
    # divergent-copy markers the rule guards: embedded canonical ontology data
    # files and the source languages where a local Ontology/Canonicalizer class
    # would live. A rule-specific entry REPLACES (does not merge) the architecture
    # domain fallback, so services.yml is listed explicitly here.
    "ARCH-006": (
        "services.yml",
        "**/services.yml",
        "**/ontology_complete.yaml",
        "**/value_mappings.json",
        "**/ontology.py",
        "src/**/*.py",
        "backend/**/*.py",
        "src/**/*.ts",
        "src/**/*.go",
        "services/**/*.py",
        "services/**/*.go",
    ),
    "SVC-004": (
        "scripts/deploy-dev.sh",
        "scripts/deploy-staging.sh",
        "scripts/deploy-*.sh",
        "docker-compose*.yml",
        "infra/**/deploy*.sh",
        "Dockerfile",
        "services.yml",
        "**/services.yml",
    ),
}

FALLBACK_APPLIES_TO_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    "governance": (
        "docs/**/*.md",
        "docs/DECISIONS.md",
        "docs/STATUS.md",
        # SCP's OWN enforcement core. These EXACT SCP-repo paths (deliberately
        # not a blanket scripts/** or lib/**, which would false-surface
        # governance rules on every adopter's deploy/helper scripts) let
        # resolve_domain govern changes to the policy-check gate itself under
        # the TCB-integrity rules (GOV-006/007/008) + the GOV-002/003 process
        # rules, instead of falling through to confidence 0. Adopter repos do
        # not carry these filenames (they consume the reusable workflow
        # remotely), so the exact-path form stays SCP-self-scoped.
        # FUP-APPLIES-TO-ENFORCEMENT-CORE-COVERAGE-001.
        "scripts/scp-policy-check",
        "lib/policy_check_invocation.sh",
    ),
    "architecture": (
        "src/**/*.py",
        "src/**/*.ts",
        "src/**/*.tsx",
        "frontend/**/*.ts",
        "frontend/**/*.tsx",
        "backend/**/*.py",
        # R3.0: surface architecture rules on Go (control-tower + mapp-pim are
        # heavily Go). Advisory consult only — no Rego enforcement fires on Go
        # yet (REACH-3.1). Scoped to src/ + packages/ (NOT blanket **/*.go) so
        # vendored/example Go is not flagged.
        "src/**/*.go",
        "packages/**/*.go",
        # Estate service-repo shapes: mapp-pim + Recommender lay services out
        # as services/<name>/ at repo root (services/enrichment, services/search,
        # services/channel-export). Governed data-contract changes (ARCH-005
        # feed envelope, ARCH-006 ontology consumption, reco index mappings)
        # live under these paths in adopter worktrees.
        "services/**/*.py",
        "services/**/*.go",
        "services/**/*.ts",
    ),
    "ux": (
        "frontend/**/*.tsx",
        "frontend/**/*.jsx",
        "app/**/*.tsx",
        "app/**/*.jsx",
        "**/*.css",
        "**/*.scss",
    ),
    "design": (
        "frontend/**/*.tsx",
        "frontend/**/*.jsx",
        "app/**/*.tsx",
        "app/**/*.jsx",
        "design-system/**",
        "**/*.css",
        "**/*.scss",
    ),
    "product": (
        "docs/plans/**/*.md",
        "docs/reviews/**/*.md",
        "frontend/**/*.tsx",
        "app/**/*.tsx",
    ),
    "service-lifecycle": (
        "services.yml",
        "**/services.yml",
    ),
}


def applies_to_for_rule(
    rule_id: str,
    domain: str,
    declared: list[str] | tuple[str, ...] | None = None,
) -> list[str]:
    """Return the effective applies_to globs for a rule.

    A declared list wins outright; otherwise a rule-specific fallback REPLACES
    the domain fallback (it does not merge with it).
    """
    if isinstance(declared, (list, tuple)) and all(isinstance(item, str) for item in declared):
        return list(dict.fromkeys(declared))

    fallback = FALLBACK_APPLIES_TO_BY_RULE_ID.get(rule_id)
    if fallback is None:
        fallback = FALLBACK_APPLIES_TO_BY_DOMAIN.get(domain, ())
    return list(fallback)


def glob_matches(path: str, pattern: str) -> bool:
    """Match a repo-relative posix path against an applies_to glob.

    ``**`` matches zero or more whole path segments; ``*``/``?`` never cross a
    ``/`` (per-segment fnmatch). Matching is case-sensitive.
    """
    parts = tuple(part for part in path.replace("\\", "/").split("/") if part)
    pattern_parts = tuple(pattern.split("/"))
    return _match_segments(parts, pattern_parts)


def _match_segments(parts: tuple[str, ...], pattern_parts: tuple[str, ...]) -> bool:
    # Collapse consecutive "**" (equivalent) and memoise on (path index,
    # pattern index) so patterns with several "**" segments stay polynomial
    # instead of fanning out exponentially over deep paths.
    collapsed: list[str] = []
    for part in pattern_parts:
        if part == "**" and collapsed and collapsed[-1] == "**":
            continue
        collapsed.append(part)

    memo: dict[tuple[int, int], bool] = {}

    def match(path_index: int, pattern_index: int) -> bool:
        key = (path_index, pattern_index)
        if key in memo:
            return memo[key]
        if pattern_index == len(collapsed):
            result = path_index == len(parts)
        elif collapsed[pattern_index] == "**":
            result = any(
                match(next_index, pattern_index + 1)
                for next_index in range(path_index, len(parts) + 1)
            )
        elif path_index == len(parts):
            result = False
        else:
            result = fnmatchcase(parts[path_index], collapsed[pattern_index]) and match(
                path_index + 1, pattern_index + 1
            )
        memo[key] = result
        return result

    return match(0, 0)
