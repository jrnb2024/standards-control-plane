"""Golden-file tests for `scripts/generate-scorecard-report.py`.

Each fixture under `tests/scorecard-report/fixtures/<name>/` carries:
- `index.json` — input scorecard index.
- `expected.md` — canonical expected markdown output.

The generator MUST produce byte-identical output to `expected.md` for
deterministic CI behaviour. Closes WP-SCP-023 023D AC (vi).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "scripts" / "generate-scorecard-report.py"
FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"


def _collect_fixture_dirs() -> list[Path]:
    if not FIXTURES_ROOT.exists():
        return []
    return sorted(p for p in FIXTURES_ROOT.iterdir() if p.is_dir() and (p / "index.json").is_file())


@pytest.mark.parametrize(
    "fixture_dir",
    _collect_fixture_dirs(),
    ids=lambda p: p.name,
)
def test_generator_matches_golden(fixture_dir: Path, tmp_path: Path) -> None:
    index_path = fixture_dir / "index.json"
    expected_path = fixture_dir / "expected.md"
    out_path = tmp_path / "report.md"
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--index", str(index_path), "--out", str(out_path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, f"generator failed: {result.stderr}"
    actual = out_path.read_text(encoding="utf-8")
    expected = expected_path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"generated report differs from golden file {expected_path}.\n"
        f"To update: regenerate with the same generator command, verify "
        f"the diff is intended, then commit."
    )


@pytest.mark.parametrize(
    "fixture_dir",
    _collect_fixture_dirs(),
    ids=lambda p: p.name,
)
def test_report_excludes_waiver_content(fixture_dir: Path) -> None:
    """Per WP-SCP-023 plan-doc invariant 2."""
    expected = (fixture_dir / "expected.md").read_text(encoding="utf-8")
    forbidden = ['"reason"', '"approved_by"', '"waiver_id"']
    for key in forbidden:
        assert key not in expected, (
            f"WP-SCP-023 plan-doc invariant 2 violation: "
            f"{fixture_dir / 'expected.md'} contains forbidden key {key}"
        )


def test_missing_index_fails_with_clear_error(tmp_path: Path) -> None:
    out_path = tmp_path / "report.md"
    nonexistent = tmp_path / "missing.json"
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--index", str(nonexistent), "--out", str(out_path)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode != 0
    assert "scorecard index not found" in result.stderr


def test_unknown_schema_version_rejected(tmp_path: Path) -> None:
    """Closes 023D R3 COR-R3-nit-001: regression test for the
    fix-round-2 schema_version guard. An index with unknown
    schema_version must produce exit 1 + the documented stderr error
    rather than silently rendering a malformed report.
    """
    bad_index = tmp_path / "index.json"
    bad_index.write_text(
        json.dumps(
            {
                "schema_version": "999.0",
                "aggregated_at": "2026-05-03T00:00:00Z",
                "aggregator_run_id": 0,
                "adopters": [],
            }
        ),
        encoding="utf-8",
    )
    out_path = tmp_path / "report.md"
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--index", str(bad_index), "--out", str(out_path)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode != 0
    assert "unsupported scorecard-index schema_version" in result.stderr
    assert not out_path.exists(), (
        "generator must NOT write the report when schema_version is "
        "unknown — would silently produce a malformed report"
    )
