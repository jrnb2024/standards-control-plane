#!/usr/bin/env python3
"""Generate the SCP scorecard markdown report from `output/scorecards/index.json`.

Closes WP-SCP-023 023D: produces `docs/scorecards/<YYYY-MM-DD>.md` with
adopter table + drift section + footer per plan-doc §5. Deterministic
output for golden-file testing — sorts adopters by repo, no embedded
timestamps in the body except the canonical `aggregated_at` from the
index.

Invoked by the aggregator workflow's commit job after the index is
written. Operators can run manually: `python3 scripts/generate-scorecard-report.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX_PATH = REPO_ROOT / "output" / "scorecards" / "index.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "scorecards"


def _format_status_cell(adopter: dict) -> str:
    status = adopter.get("status", "?")
    if status == "verified":
        verdict = adopter.get("verdict", "?")
        return f"✅ verified ({verdict})"
    if status == "verification_failure":
        return "❌ verification_failure"
    if status == "unreachable":
        return "⚠️ unreachable"
    if status == "no_emit":
        return "⚠️ no_emit"
    return f"? {status}"


def _format_rule_counts_cell(adopter: dict) -> str:
    """Render rule_counts as compact ' SCP-R-001: 2d/1w/0r ...' string.

    d = denies, w = waived, r = rule_config_disabled (boolean → 1/0).
    Only includes rules with non-zero raw_findings or non-false
    rule_config_disabled. Order: ascending rule_id.
    """
    rule_counts = adopter.get("rule_counts", {})
    if not rule_counts:
        return "—"
    parts = []
    for rule_id in sorted(rule_counts.keys()):
        c = rule_counts[rule_id]
        rfd = c.get("raw_findings", 0)
        d = c.get("denies", 0)
        w = c.get("waived", 0)
        r = 1 if c.get("rule_config_disabled", False) else 0
        if rfd == 0 and not c.get("rule_config_disabled", False):
            continue
        parts.append(f"`{rule_id}: {rfd}f/{d}d/{w}w/{r}rcd`")
    return " ".join(parts) if parts else "—"


def _format_waivers_cell(adopter: dict) -> str:
    agg = adopter.get("waivers_aggregate", {})
    active = agg.get("active_count", 0)
    expiring = agg.get("expiring_within_30d", 0)
    if active == 0:
        return "—"
    return f"{active} active ({expiring} expiring ≤30d)"


def _format_rule_config_cell(adopter: dict) -> str:
    agg = adopter.get("rule_config_aggregate", {})
    disabled = agg.get("disabled_rules", []) or []
    expiring = agg.get("expiring_within_30d", 0)
    if not disabled:
        return "—"
    return f"{len(disabled)} disabled ({expiring} expiring ≤30d)"


def render(index: dict) -> str:
    """Render the scorecard index as a markdown report.

    Deterministic: sorts adopters by repo; no embedded current-timestamp
    in the body (only the canonical `aggregated_at` from the index).
    """
    aggregated_at = index.get("aggregated_at", "?")
    aggregator_run_id = index.get("aggregator_run_id", 0)
    adopters = sorted(index.get("adopters", []), key=lambda a: a.get("repo", ""))

    # Counts for the header
    total = len(adopters)
    verified = sum(1 for a in adopters if a.get("status") == "verified")

    lines: list[str] = []
    lines.append(f"# SCP Cross-Repo Scorecard — `{aggregated_at}`")
    lines.append("")
    lines.append(
        f"Aggregator run: [`{aggregator_run_id}`](https://github.com/jrnb2024/standards-control-plane-/actions/runs/{aggregator_run_id})"
    )
    lines.append("")
    lines.append(
        f"**Adopters opted in:** {total} | **Verified:** {verified} | "
        f"**Verification failures + unreachable + no-emit:** {total - verified}"
    )
    lines.append("")
    lines.append(
        "Index trust: rooted in git's required-signed-commits + "
        "`output/scorecards/** @jrnb2024` CODEOWNERS + branch-protection on main "
        "(per WP-SCP-023 023C / D-042). Per-emit OIDC verification via "
        "`gh attestation verify --signer-workflow`. "
        "**This report NEVER carries waiver content** "
        "(`reason` / `approved_by` / `waiver_id` strings) — "
        "WP-SCP-023 plan-doc invariant 2."
    )
    lines.append("")

    if not adopters:
        lines.append("## Adopters")
        lines.append("")
        lines.append(
            "*No adopters opted in yet. Adopters PR additions to "
            "`docs/scorecards/opt-in-registry.yaml` to participate. "
            "Threshold A target: ≥3 adopters opted in (slice 023E).*"
        )
        lines.append("")
    else:
        lines.append("## Adopters")
        lines.append("")
        lines.append(
            "| Repo | Status | SCP version | Rule counts (f/d/w/rcd) | Waivers (active) | Rule-config (disabled) |"
        )
        lines.append("|---|---|---|---|---|---|")
        for adopter in adopters:
            repo = adopter.get("repo", "?")
            scp_version = adopter.get("scp_version", "—")
            lines.append(
                f"| `{repo}` "
                f"| {_format_status_cell(adopter)} "
                f"| {scp_version} "
                f"| {_format_rule_counts_cell(adopter)} "
                f"| {_format_waivers_cell(adopter)} "
                f"| {_format_rule_config_cell(adopter)} |"
            )
        lines.append("")

        # Failure detail section
        failures = [a for a in adopters if a.get("status") != "verified"]
        if failures:
            lines.append("## Verification failures + unreachable + no-emit")
            lines.append("")
            for adopter in failures:
                repo = adopter.get("repo", "?")
                status = adopter.get("status", "?")
                error = adopter.get("error", "(no error string)")
                lines.append(f"### `{repo}` — `{status}`")
                lines.append("")
                lines.append(f"> {error}")
                lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "*Report auto-generated by `scripts/generate-scorecard-report.py` "
        "from `output/scorecards/index.json` per WP-SCP-023 023D. "
        "Schema: `schemas/scorecard-index.schema.json`. "
        "Cell legend: `f` = raw_findings, `d` = effective denies (post-suppression), "
        "`w` = waived, `rcd` = rule_config_disabled (1=true).*"
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SCP scorecard markdown report")
    parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help=f"Path to scorecard index JSON (default: {DEFAULT_INDEX_PATH})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output markdown path. Default: docs/scorecards/<aggregated_at-date>.md",
    )
    args = parser.parse_args()

    if not args.index.is_file():
        print(f"::error file={args.index},title=SCP-E001::scorecard index not found", file=sys.stderr)
        return 1

    index = json.loads(args.index.read_text(encoding="utf-8"))
    aggregated_at = index.get("aggregated_at", "1970-01-01T00:00:00Z")
    # Date prefix from aggregated_at (YYYY-MM-DD).
    try:
        date_prefix = aggregated_at[:10]
        # Validate it's a date.
        datetime.strptime(date_prefix, "%Y-%m-%d")
    except (ValueError, TypeError):
        date_prefix = "unknown-date"

    out = args.out or (DEFAULT_REPORT_DIR / f"{date_prefix}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(index), encoding="utf-8")
    print(f"Wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
