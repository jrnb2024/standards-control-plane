"""Validate hand-crafted scorecard-emit fixture pairs against the schema.

Closes WP-SCP-023 023B AC (vii)+(viii). Each fixture under
`tests/scorecard-emit/fixtures/<name>/` carries:

- `policy-check-summary.json` — the input the workflow's emitter step
  would consume (schema validates against
  `schemas/policy-check-summary.schema.json`).
- `expected-scorecard-emit.json` — the canonical expected emit shape
  the workflow's emitter step would produce. This file MUST validate
  against `schemas/scorecard-emit.schema.json`.

Per WP-SCP-023 plan-doc invariant 2, no fixture's
`expected-scorecard-emit.json` may include `reason`, `approved_by`, or
`waiver_id` strings — the schema enforces this via
`additionalProperties: false` at every level.

The end-to-end transformation (policy-check-summary → scorecard-emit)
is integration-tested by the workflow-selftest harness when the SCP
self-dogfood wrapper opts in to `scorecard-emit: true` (forward-compat
to slice 023C). This test layer validates schema conformance of the
canonical expected emits, which is the load-bearing invariant for
slice 023B's contract with adopters.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"
SCORECARD_SCHEMA_PATH = REPO_ROOT / "schemas" / "scorecard-emit.schema.json"
SUMMARY_SCHEMA_PATH = REPO_ROOT / "schemas" / "policy-check-summary.schema.json"


def _collect_fixture_dirs() -> list[Path]:
    if not FIXTURES_ROOT.exists():
        return []
    return sorted(p for p in FIXTURES_ROOT.iterdir() if p.is_dir())


def _scorecard_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(SCORECARD_SCHEMA_PATH.read_text())
    return jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )


def _summary_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(SUMMARY_SCHEMA_PATH.read_text())
    return jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )


@pytest.mark.parametrize(
    "fixture_dir",
    _collect_fixture_dirs(),
    ids=lambda p: p.name,
)
def test_expected_scorecard_emit_validates_against_schema(fixture_dir: Path) -> None:
    """The expected-scorecard-emit.json must validate against the schema."""
    expected_path = fixture_dir / "expected-scorecard-emit.json"
    assert expected_path.is_file(), f"missing {expected_path}"
    expected = json.loads(expected_path.read_text())
    _scorecard_validator().validate(expected)


@pytest.mark.parametrize(
    "fixture_dir",
    _collect_fixture_dirs(),
    ids=lambda p: p.name,
)
def test_input_policy_check_summary_validates_against_schema(fixture_dir: Path) -> None:
    """The fixture's policy-check-summary.json must validate against the
    pre-existing schema — the emitter consumes a real summary, so the
    test corpus must use real-shape inputs."""
    summary_path = fixture_dir / "policy-check-summary.json"
    assert summary_path.is_file(), f"missing {summary_path}"
    summary = json.loads(summary_path.read_text())
    _summary_validator().validate(summary)


@pytest.mark.parametrize(
    "fixture_dir",
    _collect_fixture_dirs(),
    ids=lambda p: p.name,
)
def test_expected_scorecard_emit_excludes_waiver_content(fixture_dir: Path) -> None:
    """Per WP-SCP-023 plan-doc invariant 2: NO waiver content
    (`reason`, `approved_by`, `waiver_id` strings) crosses the
    boundary. The schema's `additionalProperties: false` enforces this
    at validation time, but we additionally scan the expected emit
    text for any of those keys to catch a future schema-drift mistake
    where the constraint is loosened.
    """
    expected_path = fixture_dir / "expected-scorecard-emit.json"
    raw = expected_path.read_text()
    forbidden_keys = ['"reason"', '"approved_by"', '"waiver_id"']
    for key in forbidden_keys:
        assert key not in raw, (
            f"WP-SCP-023 plan-doc invariant 2 violation: "
            f"{expected_path} contains forbidden key {key} — "
            f"waiver content must NEVER cross the cross-repo aggregator boundary"
        )
