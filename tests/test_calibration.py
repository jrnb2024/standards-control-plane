from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from standards_control_plane.calibration import (
    build_false_positive_summary,
    write_false_positive_summary,
)
from standards_control_plane.findings import EvidenceRecord, FindingRecord, FindingsStore
from standards_control_plane.resources import output_dir
from standards_control_plane.schema_tools import validate_with_schema


def _history_store_with_false_positive() -> FindingsStore:
    return FindingsStore(
        store_version="0.1.0",
        generated_at="2026-04-12T00:00:00Z",
        findings=(
            FindingRecord(
                finding_id="F-PROD-002-ops-internals",
                domain="product",
                severity="medium",
                status="false_positive",
                title="Action alignment drift",
                summary="Internal action language was over-flagged in a migration console.",
                evidence=(
                    EvidenceRecord(
                        path="fixtures/product-drift-console/frontend/app/internals/page.tsx",
                        evidence_class="direct_file",
                        locator="internal-language action marker",
                        snippet_ref=None,
                    ),
                ),
                area_id="ops-internals",
                suggested_remediation=("Tune wording heuristic.",),
                confidence=0.8,
                confidence_class="medium",
                detected_by="product-evaluator",
                standards_version="2026-04-12",
                created_at="2026-04-12T00:00:00Z",
                updated_at="2026-04-12T00:00:00Z",
                rule_id="PROD-002",
            ),
        ),
    )


def test_false_positive_summary_builds_and_validates() -> None:
    summary = build_false_positive_summary(_history_store_with_false_positive())
    validate_with_schema(summary, "false-positive-summary.schema.json")
    assert summary["total_false_positive_count"] == 1
    assert summary["by_rule"][0]["rule_id"] == "PROD-002"


def test_write_false_positive_summary_persists_summary(tmp_path: Path) -> None:
    history_store = _history_store_with_false_positive()
    output_root = tmp_path / "output"
    summary_path = write_false_positive_summary(history_store, base_output_dir=output_root)
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    validate_with_schema(payload, "false-positive-summary.schema.json")
    assert payload["total_false_positive_count"] == 1


def test_calibration_cli_prints_current_summary() -> None:
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src")

    history_store = FindingsStore(
        store_version="0.1.0",
        generated_at="2026-04-11T00:00:00Z",
        findings=(),
    )
    summary_path = write_false_positive_summary(history_store, base_output_dir=output_dir())
    assert summary_path.exists()

    completed = subprocess.run(
        [sys.executable, "-m", "standards_control_plane.cli", "calibration"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(completed.stdout)
    validate_with_schema(payload, "false-positive-summary.schema.json")
    assert "total_false_positive_count" in payload
