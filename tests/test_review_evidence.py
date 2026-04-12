from __future__ import annotations

from standards_control_plane.review_evidence import (
    load_review_evidence_records,
    parse_review_evidence_file,
    select_historical_reviews,
)
from standards_control_plane.schema_tools import validate_with_schema


def test_parse_review_evidence_file_loads_seeded_returns_record() -> None:
    record = parse_review_evidence_file(
        "fixtures/returns-pilot/docs/reviews/WP-RET-014/review_findings.md"
    )
    assert record is not None
    assert record.review_id == "WP-RET-014"
    assert record.area_id == "returns-exceptions"
    assert record.reviewed_paths == (
        "fixtures/returns-pilot/frontend/app/exceptions/page.tsx",
        "fixtures/returns-pilot/frontend/app/shared/filters.ts",
    )
    assert record.findings[0].finding_id == "F-RET-014-001"


def test_load_review_evidence_records_skips_legacy_unstructured_files() -> None:
    records = load_review_evidence_records(
        [
            "fixtures/review-evidence-legacy/docs/reviews/WP-LEG-001/review_findings.md",
            "fixtures/returns-pilot/docs/reviews/WP-RET-014/review_findings.md",
        ]
    )
    assert [record.review_id for record in records] == ["WP-RET-014"]


def test_select_historical_reviews_prefers_exact_area_match_before_path_overlap() -> None:
    reviews = select_historical_reviews(
        area_id="returns-exceptions",
        request_paths=["fixtures/returns-pilot/frontend/app/exceptions/page.tsx"],
    )
    assert [review["review_id"] for review in reviews[:3]] == [
        "WP-RET-014",
        "WP-SCP-004",
        "WP-OVR-001",
    ]


def test_select_historical_reviews_returns_empty_list_when_no_match_exists() -> None:
    reviews = select_historical_reviews(
        area_id="signals-api-drift",
        request_paths=["fixtures/architecture-api-drift/frontend/app/orders/page.tsx"],
    )
    assert reviews == []


def test_seeded_review_evidence_block_validates_against_schema() -> None:
    record = parse_review_evidence_file(
        "fixtures/returns-pilot/docs/reviews/WP-RET-014/review_findings.md"
    )
    assert record is not None
    validate_with_schema(
        {
            "review_id": record.review_id,
            "area_id": record.area_id,
            "reviewed_at": record.reviewed_at,
            "summary": record.summary,
            "reviewed_paths": list(record.reviewed_paths),
            "findings": [
                {
                    "finding_id": finding.finding_id,
                    "status": finding.status,
                    "summary": finding.summary,
                    "domain": finding.domain,
                }
                for finding in record.findings
            ],
        },
        "review-evidence.schema.json",
    )
