"""False-positive calibration summary generation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .findings import FindingRecord, FindingsStore, load_findings_store
from .resources import output_dir
from .schema_tools import validate_with_schema

FALSE_POSITIVE_SUMMARY_FILENAME = "false-positive-summary.json"


def _false_positive_summary_path(base_output_dir: Path | None = None) -> Path:
    root = base_output_dir or output_dir()
    return root / "findings" / FALSE_POSITIVE_SUMMARY_FILENAME


def _rule_key(finding: FindingRecord) -> tuple[str, str]:
    return finding.domain, finding.rule_id or "unmapped"


def build_false_positive_summary(history_store: FindingsStore) -> dict[str, Any]:
    false_positives = [
        finding for finding in history_store.findings if finding.status == "false_positive"
    ]
    grouped: dict[tuple[str, str], list[FindingRecord]] = {}
    for finding in false_positives:
        grouped.setdefault(_rule_key(finding), []).append(finding)

    by_rule = [
        {
            "domain": domain,
            "rule_id": rule_id,
            "count": len(findings),
            "latest_at": max(finding.updated_at for finding in findings),
            "confidence_classes": sorted({finding.confidence_class for finding in findings}),
        }
        for (domain, rule_id), findings in grouped.items()
    ]
    by_rule.sort(key=lambda item: (-int(item["count"]), str(item["domain"]), str(item["rule_id"])))

    recent_false_positives = sorted(
        false_positives,
        key=lambda finding: (finding.updated_at, finding.finding_id),
        reverse=True,
    )[:10]

    calibration_actions: list[str] = []
    if by_rule:
        calibration_actions.append(
            "Review rules with repeated false positives before increasing enforcement weight."
        )
    else:
        calibration_actions.append(
            "No false positives are currently recorded in persisted history."
        )

    summary = {
        "generated_at": history_store.generated_at,
        "total_false_positive_count": len(false_positives),
        "by_rule": by_rule,
        "recent_false_positives": [finding.to_dict() for finding in recent_false_positives],
        "calibration_actions": calibration_actions,
    }
    validate_with_schema(summary, "false-positive-summary.schema.json")
    return summary


def write_false_positive_summary(
    history_store: FindingsStore,
    *,
    base_output_dir: Path | None = None,
) -> Path:
    summary = build_false_positive_summary(history_store)
    target_path = _false_positive_summary_path(base_output_dir)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=target_path.parent,
        delete=False,
        prefix=f".{target_path.name}.",
        suffix=".tmp",
    ) as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
        staged_path = Path(handle.name)

    backup_path: Path | None = None
    if target_path.exists():
        with NamedTemporaryFile(
            mode="wb",
            dir=target_path.parent,
            delete=False,
            prefix=f".{target_path.name}.",
            suffix=".bak",
        ) as handle:
            handle.write(target_path.read_bytes())
            backup_path = Path(handle.name)

    try:
        os.replace(staged_path, target_path)
        staged_path = None
    except Exception:
        if backup_path is not None:
            os.replace(backup_path, target_path)
            backup_path = None
        raise
    finally:
        if staged_path is not None and staged_path.exists():
            staged_path.unlink()
        if backup_path is not None and backup_path.exists():
            backup_path.unlink()
    return target_path


def load_false_positive_summary(base_output_dir: Path | None = None) -> dict[str, Any]:
    summary_path = _false_positive_summary_path(base_output_dir)
    if summary_path.exists():
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        validate_with_schema(payload, "false-positive-summary.schema.json")
        return payload
    history_store = load_findings_store(
        (base_output_dir or output_dir()) / "findings" / "findings-history.json"
    )
    return build_false_positive_summary(history_store)
