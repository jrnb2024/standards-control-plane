from __future__ import annotations

from standards_control_plane.consult import build_consult_response


def test_frontend_consult_orders_patterns_before_rules_and_prefers_frontend_domains() -> None:
    request = {
        "mode": "consult",
        "question": "How should I implement a review workspace screen?",
        "domains": ["ux", "design", "architecture", "product"],
        "area_id": "returns-review",
        "paths": ["fixtures/product-stable-review/frontend/app/review/page.tsx"],
        "task_context": {
            "feature_summary": "Build a review screen with actions, detail, and stable states.",
            "subsystem": "returns",
        },
    }
    response = build_consult_response(request)
    assert list(response)[:4] == [
        "request_id",
        "domains",
        "approved_patterns",
        "open_findings",
    ]
    first_four = [pattern["pattern_id"] for pattern in response["approved_patterns"][:4]]
    assert set(first_four[:2]) == {"workspace-page-template", "review-flow-template"}
    assert set(first_four[2:4]) == {"table-screen-pattern", "form-screen-pattern"}
