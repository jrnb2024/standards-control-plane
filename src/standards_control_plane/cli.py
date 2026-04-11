"""CLI scaffold for the Standards Control Plane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .consult import build_consult_response
from .findings import load_findings_store
from .registry import load_registry
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


def _stub_audit_result(request: dict[str, Any]) -> dict[str, Any]:
    scores = {domain: 0 for domain in request["domains"]}
    result = {
        "audit_id": "audit-scaffold-001",
        "scope": request["scope"],
        "scores": scores,
        "summary": {
            "high_severity_count": 0,
            "medium_severity_count": 0,
            "low_severity_count": 0,
        },
        "findings": [],
        "drift": [],
        "regressions": [],
        "recommended_actions": [
            "Implement governance and architecture evaluators.",
            "Connect the audit engine to the findings store.",
        ],
        "generated_at": "2026-04-11T00:00:00Z",
    }
    validate_with_schema(result, "audit-result.schema.json")
    return result


def cmd_consult(args: argparse.Namespace) -> int:
    request = _read_request(args.request, "consult-request.schema.json")
    _print_json(build_consult_response(request))
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    request = _read_request(args.request, "audit-request.schema.json")
    _print_json(_stub_audit_result(request))
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
    print(report_path.read_text(encoding="utf-8"))
    return 0


def cmd_show_registry(args: argparse.Namespace) -> int:
    registry_path = standards_dir() / "standards-index.json"
    _print_json(load_registry(registry_path).to_dict())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standards Control Plane scaffold CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    consult = subparsers.add_parser("consult", help="Validate a consult request and emit a scaffold response")
    consult.add_argument("--request", required=True, help="Path to consult request JSON")
    consult.set_defaults(func=cmd_consult)

    audit = subparsers.add_parser("audit", help="Validate an audit request and emit a scaffold result")
    audit.add_argument("--request", required=True, help="Path to audit request JSON")
    audit.set_defaults(func=cmd_audit)

    findings = subparsers.add_parser("findings", help="Print the current open findings file")
    findings.set_defaults(func=cmd_findings)

    report = subparsers.add_parser("report", help="Print the latest markdown report")
    report.set_defaults(func=cmd_report)

    registry = subparsers.add_parser("show-registry", help="Print the top-level standards registry index")
    registry.set_defaults(func=cmd_show_registry)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
