"""CLI scaffold for the Standards Control Plane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .audit import build_audit_result
from .calibration import load_false_positive_summary, write_false_positive_summary
from .consult import build_consult_response
from .findings import load_findings_store, persist_audit_findings
from .registry import load_registry
from .reports import (
    extract_generated_at,
    extract_history_signature,
    extract_open_signature,
    report_source_signatures,
    write_audit_reports,
)
from .resources import output_dir, standards_dir
from .schema_tools import load_json_file, validate_with_schema


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def _read_request(path_value: str, schema_name: str) -> dict[str, Any]:
    payload = load_json_file(Path(path_value))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path_value}")
    validate_with_schema(payload, schema_name)
    return payload


def cmd_consult(args: argparse.Namespace) -> int:
    request = _read_request(args.request, "consult-request.schema.json")
    _print_json(build_consult_response(request))
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    request = _read_request(args.request, "audit-request.schema.json")
    result = build_audit_result(request)
    if args.write_output:
        open_store, history_store = persist_audit_findings(result)
        write_audit_reports(
            result,
            open_store=open_store,
            history_store=history_store,
        )
        write_false_positive_summary(history_store)
    _print_json(result)
    return 0


def cmd_findings(args: argparse.Namespace) -> int:
    findings_path = output_dir() / "findings" / "open-findings.json"
    if not findings_path.exists():
        print(f"Findings file not found: {findings_path}", file=sys.stderr)
        return 1
    _print_json(load_findings_store(findings_path).to_dict())
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    report_path = output_dir() / "reports" / "latest-review.md"
    if not report_path.exists():
        print(f"Report file not found: {report_path}", file=sys.stderr)
        return 1
    report_text = report_path.read_text(encoding="utf-8")
    report_generated_at = extract_generated_at(report_text)
    try:
        open_store = load_findings_store(output_dir() / "findings" / "open-findings.json")
        history_store = load_findings_store(output_dir() / "findings" / "findings-history.json")
    except Exception as error:
        print(f"Unable to validate report freshness: {error}", file=sys.stderr)
        return 1

    open_signature = extract_open_signature(report_text)
    history_signature = extract_history_signature(report_text)
    expected_open_signature, expected_history_signature = report_source_signatures(
        open_store,
        history_store,
    )
    if (
        report_generated_at is None
        or report_generated_at != open_store.generated_at
        or open_signature is None
        or history_signature is None
        or open_signature != expected_open_signature
        or history_signature != expected_history_signature
    ):
        print(
            "Latest review is stale or malformed; refresh it with `audit --write-output`.",
            file=sys.stderr,
        )
        return 1
    print(report_text)
    return 0


def cmd_show_registry(args: argparse.Namespace) -> int:
    registry_path = standards_dir() / "standards-index.json"
    _print_json(load_registry(registry_path).to_dict())
    return 0


def cmd_calibration(args: argparse.Namespace) -> int:
    _print_json(load_false_positive_summary())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standards Control Plane CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    consult = subparsers.add_parser("consult", help="Validate a consult request and emit a scaffold response")
    consult.add_argument("--request", required=True, help="Path to consult request JSON")
    consult.set_defaults(func=cmd_consult)

    audit = subparsers.add_parser("audit", help="Validate an audit request and emit a live audit result")
    audit.add_argument("--request", required=True, help="Path to audit request JSON")
    audit.add_argument(
        "--write-output",
        action="store_true",
        help="Persist reconciled open and history findings stores after audit.",
    )
    audit.set_defaults(func=cmd_audit)

    findings = subparsers.add_parser("findings", help="Print the current open findings file")
    findings.set_defaults(func=cmd_findings)

    report = subparsers.add_parser("report", help="Print the latest markdown report")
    report.set_defaults(func=cmd_report)

    registry = subparsers.add_parser("show-registry", help="Print the top-level standards registry index")
    registry.set_defaults(func=cmd_show_registry)

    calibration = subparsers.add_parser("calibration", help="Print the current false-positive calibration summary")
    calibration.set_defaults(func=cmd_calibration)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
