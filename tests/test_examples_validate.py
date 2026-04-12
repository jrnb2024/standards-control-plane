from __future__ import annotations

from standards_control_plane.resources import examples_dir, output_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema


def test_consult_request_example_validates() -> None:
    payload = load_json_file(examples_dir() / "consult-request.json")
    validate_with_schema(payload, "consult-request.schema.json")


def test_consult_response_example_validates() -> None:
    payload = load_json_file(examples_dir() / "consult-response.json")
    validate_with_schema(payload, "consult-response.schema.json")


def test_audit_request_example_validates() -> None:
    payload = load_json_file(examples_dir() / "audit-request.json")
    validate_with_schema(payload, "audit-request.schema.json")


def test_audit_result_example_validates() -> None:
    payload = load_json_file(examples_dir() / "audit-result.json")
    validate_with_schema(payload, "audit-result.schema.json")


def test_extracted_scope_example_validates() -> None:
    payload = load_json_file(examples_dir() / "extracted-scope-returns-pilot.json")
    validate_with_schema(payload, "extracted-scope.schema.json")


def test_project_area_example_validates() -> None:
    payload = load_json_file(examples_dir() / "project-area-returns-exceptions.json")
    validate_with_schema(payload, "project-area.schema.json")


def test_open_findings_store_validates() -> None:
    payload = load_json_file(output_dir() / "findings" / "open-findings.json")
    validate_with_schema(payload, "findings-store.schema.json")


def test_history_findings_store_validates() -> None:
    payload = load_json_file(output_dir() / "findings" / "findings-history.json")
    validate_with_schema(payload, "findings-store.schema.json")


def test_false_positive_summary_validates() -> None:
    payload = load_json_file(output_dir() / "findings" / "false-positive-summary.json")
    validate_with_schema(payload, "false-positive-summary.schema.json")


def test_waivers_file_validates() -> None:
    payload = load_json_file(output_dir() / "findings" / "waivers.json")
    validate_with_schema(payload, "waivers-file.schema.json")


def test_returns_area_summary_validates() -> None:
    payload = load_json_file(output_dir() / "findings" / "area-summaries" / "returns.json")
    validate_with_schema(payload, "area-summary.schema.json")
