"""CLI scaffold for the Standards Control Plane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .audit import build_audit_result
from .calibration import load_false_positive_summary, write_false_positive_summary
from .changed_audit import build_changed_file_audit_result
from .ci_outputs import (
    latest_ci_json_path,
    latest_ci_markdown_path,
    load_ci_output,
    write_ci_outputs,
)
from .consult import build_consult_response
from .control_tower import (
    estate_dashboard_path,
    load_control_tower_surface,
    load_estate_dashboard,
    write_control_tower_outputs,
)
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
from .service import serve


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def _read_request(path_value: str, schema_name: str) -> dict[str, Any]:
    payload = load_json_file(Path(path_value))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path_value}")
    validate_with_schema(payload, schema_name)
    return payload


def _overlay_paths(values: list[str] | None) -> list[Path]:
    return [Path(value) for value in values or []]


def cmd_consult(args: argparse.Namespace) -> int:
    request = _read_request(args.request, "consult-request.schema.json")
    _print_json(
        build_consult_response(
            request,
            registry_snapshot=load_registry(overlay_paths=_overlay_paths(args.overlay)),
        )
    )
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    request = _read_request(args.request, "audit-request.schema.json")
    registry_snapshot = load_registry(overlay_paths=_overlay_paths(args.overlay))
    result = build_audit_result(request, registry_snapshot=registry_snapshot)
    if args.write_output:
        open_store, history_store = persist_audit_findings(result)
        write_audit_reports(
            result,
            open_store=open_store,
            history_store=history_store,
        )
        write_false_positive_summary(history_store)
        ci_json_path, _ = write_ci_outputs(result, source_mode="audit")
        write_control_tower_outputs(
            result,
            open_store=open_store,
            ci_output=load_ci_output(ci_json_path),
        )
    _print_json(result)
    return 0


def cmd_findings(args: argparse.Namespace) -> int:
    findings_path = output_dir() / "findings" / "open-findings.json"
    if not findings_path.exists():
        print(f"Findings file not found: {findings_path}", file=sys.stderr)
        return 1
    _print_json(load_findings_store(findings_path).to_dict())
    return 0


def _parse_domains(value: str) -> list[str]:
    domains = [item.strip() for item in value.split(",") if item.strip()]
    if not domains:
        raise ValueError("At least one domain is required")
    return domains


def cmd_audit_changed(args: argparse.Namespace) -> int:
    registry_snapshot = load_registry(overlay_paths=_overlay_paths(args.overlay))
    result = build_changed_file_audit_result(
        base_ref=args.base_ref,
        head_ref=args.head_ref,
        domains=_parse_domains(args.domains),
        subsystem=args.subsystem,
        standards_version=args.standards_version,
        area_id=args.area_id,
        registry_snapshot=registry_snapshot,
    )
    if args.write_output:
        open_store, history_store = persist_audit_findings(result["audit_result"])
        write_audit_reports(
            result["audit_result"],
            open_store=open_store,
            history_store=history_store,
        )
        write_false_positive_summary(history_store)
        ci_json_path, _ = write_ci_outputs(
            result["audit_result"],
            source_mode="audit_changed",
            base_ref=args.base_ref,
            head_ref=args.head_ref,
            changed_paths=list(result["changed_paths"]),
        )
        write_control_tower_outputs(
            result["audit_result"],
            open_store=open_store,
            ci_output=load_ci_output(ci_json_path),
        )
    _print_json(result)
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
    _print_json(
        load_registry(
            registry_path,
            overlay_paths=_overlay_paths(args.overlay),
        ).to_dict()
    )
    return 0


def cmd_calibration(args: argparse.Namespace) -> int:
    _print_json(load_false_positive_summary())
    return 0


def cmd_ci(args: argparse.Namespace) -> int:
    if args.format == "json":
        ci_path = Path(args.path) if args.path else latest_ci_json_path()
        if not ci_path.exists():
            print(f"CI artifact not found: {ci_path}", file=sys.stderr)
            return 1
        try:
            _print_json(load_ci_output(ci_path))
        except Exception as error:
            print(f"Unable to load CI artifact: {error}", file=sys.stderr)
            return 1
        return 0

    ci_path = Path(args.path) if args.path else latest_ci_markdown_path()
    if not ci_path.exists():
        print(f"CI summary not found: {ci_path}", file=sys.stderr)
        return 1
    print(ci_path.read_text(encoding="utf-8"))
    return 0


def cmd_control_tower(args: argparse.Namespace) -> int:
    if args.format == "surface":
        target_path = Path(args.path) if args.path else None
        try:
            _print_json(load_control_tower_surface(target_path))
        except FileNotFoundError as error:
            print(f"Control Tower surface not found: {error.filename}", file=sys.stderr)
            return 1
        except Exception as error:
            print(f"Unable to load Control Tower surface: {error}", file=sys.stderr)
            return 1
        return 0

    dashboard_path = Path(args.path) if args.path else estate_dashboard_path()
    if not dashboard_path.exists():
        print(f"Control Tower dashboard not found: {dashboard_path}", file=sys.stderr)
        return 1
    try:
        _print_json(load_estate_dashboard(dashboard_path))
    except Exception as error:
        print(f"Unable to load Control Tower dashboard: {error}", file=sys.stderr)
        return 1
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    serve(
        host=args.host,
        port=args.port,
        overlay_paths=args.overlay,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standards Control Plane CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    consult = subparsers.add_parser(
        "consult",
        help="Validate a consult request and emit a scaffold response",
    )
    consult.add_argument("--request", required=True, help="Path to consult request JSON")
    consult.add_argument(
        "--overlay",
        action="append",
        help="Optional overlay registry directory or standards-index.json path",
    )
    consult.set_defaults(func=cmd_consult)

    audit = subparsers.add_parser(
        "audit",
        help="Validate an audit request and emit a live audit result",
    )
    audit.add_argument("--request", required=True, help="Path to audit request JSON")
    audit.add_argument(
        "--write-output",
        action="store_true",
        help="Persist reconciled open and history findings stores after audit.",
    )
    audit.add_argument(
        "--overlay",
        action="append",
        help="Optional overlay registry directory or standards-index.json path",
    )
    audit.set_defaults(func=cmd_audit)

    audit_changed = subparsers.add_parser(
        "audit-changed",
        help="Resolve changed files from git refs and emit a changed-file scoped audit result",
    )
    audit_changed.add_argument(
        "--base-ref",
        required=True,
        help="Base git ref for changed-file resolution",
    )
    audit_changed.add_argument(
        "--head-ref",
        required=True,
        help="Head git ref for changed-file resolution",
    )
    audit_changed.add_argument(
        "--domains",
        required=True,
        help="Comma-separated list of domains to evaluate",
    )
    audit_changed.add_argument(
        "--subsystem",
        required=True,
        help="Subsystem for area normalisation",
    )
    audit_changed.add_argument(
        "--standards-version",
        required=True,
        help="Standards version in YYYY-MM-DD form",
    )
    audit_changed.add_argument("--area-id", help="Optional explicit area id")
    audit_changed.add_argument(
        "--overlay",
        action="append",
        help="Optional overlay registry directory or standards-index.json path",
    )
    audit_changed.add_argument(
        "--write-output",
        action="store_true",
        help=(
            "Persist reconciled findings, reports, and calibration output after "
            "changed-file audit."
        ),
    )
    audit_changed.set_defaults(func=cmd_audit_changed)

    findings = subparsers.add_parser("findings", help="Print the current open findings file")
    findings.set_defaults(func=cmd_findings)

    report = subparsers.add_parser("report", help="Print the latest markdown report")
    report.set_defaults(func=cmd_report)

    registry = subparsers.add_parser(
        "show-registry",
        help="Print the top-level standards registry index",
    )
    registry.add_argument(
        "--overlay",
        action="append",
        help="Optional overlay registry directory or standards-index.json path",
    )
    registry.set_defaults(func=cmd_show_registry)

    calibration = subparsers.add_parser(
        "calibration",
        help="Print the current false-positive calibration summary",
    )
    calibration.set_defaults(func=cmd_calibration)

    ci = subparsers.add_parser("ci", help="Print the latest CI artifact or markdown summary")
    ci.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format for the latest CI artifact",
    )
    ci.add_argument("--path", help="Optional explicit path to a CI artifact")
    ci.set_defaults(func=cmd_ci)

    control_tower = subparsers.add_parser(
        "control-tower",
        help="Print the latest Control Tower dashboard or surface artifact",
    )
    control_tower.add_argument(
        "--format",
        choices=("dashboard", "surface"),
        default="dashboard",
        help="Output format for the latest Control Tower artifact",
    )
    control_tower.add_argument("--path", help="Optional explicit path to a Control Tower artifact")
    control_tower.set_defaults(func=cmd_control_tower)

    serve_parser = subparsers.add_parser(
        "serve",
        help="Run the lightweight HTTP service for consult and audit operations",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    serve_parser.add_argument(
        "--overlay",
        action="append",
        help="Optional overlay registry directory or standards-index.json path",
    )
    serve_parser.set_defaults(func=cmd_serve)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
