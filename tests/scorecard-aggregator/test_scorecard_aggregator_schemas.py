"""Schema-conformance + waiver-content-exclusion tests for slice 023C
aggregator.

Fixtures:
- `tests/scorecard-aggregator/fixtures/<name>/registry.yaml` — opt-in
  registry shape; validates against
  `schemas/scorecard-opt-in-registry.schema.json`. Sibling
  `expected-validation-result.txt` carries `PASS` or `FAIL` (one line).
- `tests/scorecard-aggregator/fixtures/<name>/index.json` — central
  index shape; validates against
  `schemas/scorecard-index.schema.json`. Index fixtures are all
  expected to PASS schema validation.

Per WP-SCP-023 plan-doc invariant 2 — no fixture's `index.json` may
include `reason`, `approved_by`, or `waiver_id` strings. Schema
enforces this via `additionalProperties: false`; we additionally scan
the index text to catch a future schema-drift mistake.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"
REGISTRY_SCHEMA_PATH = REPO_ROOT / "schemas" / "scorecard-opt-in-registry.schema.json"
INDEX_SCHEMA_PATH = REPO_ROOT / "schemas" / "scorecard-index.schema.json"


def _registry_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )


def _index_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(INDEX_SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )


def _collect_fixture_dirs(filename: str) -> list[Path]:
    if not FIXTURES_ROOT.exists():
        return []
    return sorted(p for p in FIXTURES_ROOT.iterdir() if p.is_dir() and (p / filename).is_file())


@pytest.mark.parametrize(
    "fixture_dir",
    _collect_fixture_dirs("registry.yaml"),
    ids=lambda p: p.name,
)
def test_registry_validates_per_expected_result(fixture_dir: Path) -> None:
    expected_path = fixture_dir / "expected-validation-result.txt"
    assert expected_path.is_file(), f"missing {expected_path}"
    expected = expected_path.read_text(encoding="utf-8").strip()
    assert expected in ("PASS", "FAIL"), (
        f"{expected_path} must contain exactly 'PASS' or 'FAIL'"
    )
    registry = yaml.safe_load((fixture_dir / "registry.yaml").read_text(encoding="utf-8"))
    if expected == "PASS":
        _registry_validator().validate(registry)
    else:
        with pytest.raises(jsonschema.ValidationError):
            _registry_validator().validate(registry)


@pytest.mark.parametrize(
    "fixture_dir",
    _collect_fixture_dirs("index.json"),
    ids=lambda p: p.name,
)
def test_index_validates_against_schema(fixture_dir: Path) -> None:
    index = json.loads((fixture_dir / "index.json").read_text(encoding="utf-8"))
    _index_validator().validate(index)


@pytest.mark.parametrize(
    "fixture_dir",
    _collect_fixture_dirs("index.json"),
    ids=lambda p: p.name,
)
def test_index_excludes_waiver_content(fixture_dir: Path) -> None:
    raw = (fixture_dir / "index.json").read_text(encoding="utf-8")
    forbidden = ['"reason"', '"approved_by"', '"waiver_id"']
    for key in forbidden:
        assert key not in raw, (
            f"WP-SCP-023 plan-doc invariant 2 violation: "
            f"{fixture_dir / 'index.json'} contains forbidden key {key} — "
            f"waiver content must NEVER cross the cross-repo aggregator boundary"
        )


def test_live_opt_in_registry_validates() -> None:
    """The live `docs/scorecards/opt-in-registry.yaml` MUST validate."""
    live = REPO_ROOT / "docs" / "scorecards" / "opt-in-registry.yaml"
    assert live.is_file(), f"missing {live}"
    registry = yaml.safe_load(live.read_text(encoding="utf-8"))
    _registry_validator().validate(registry)


def test_live_index_validates() -> None:
    """The live `output/scorecards/index.json` MUST validate."""
    live = REPO_ROOT / "output" / "scorecards" / "index.json"
    assert live.is_file(), f"missing {live}"
    index = json.loads(live.read_text(encoding="utf-8"))
    _index_validator().validate(index)
