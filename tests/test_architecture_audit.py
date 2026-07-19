from __future__ import annotations

import copy

from standards_control_plane.audit import build_audit_result
from standards_control_plane.evaluators import evaluate_architecture
from standards_control_plane.extractor import extract_scope
from standards_control_plane.normaliser import normalise_project_area


def _returns_area() -> dict[str, object]:
    return normalise_project_area(extract_scope(["fixtures/returns-pilot"]), subsystem="returns")


def _api_drift_area() -> dict[str, object]:
    return normalise_project_area(extract_scope(["fixtures/architecture-api-drift"]), subsystem="signals")


def _async_drift_area() -> dict[str, object]:
    return normalise_project_area(extract_scope(["fixtures/architecture-async-drift"]), subsystem="signals")


def test_read_repo_file_honours_repo_root_override(tmp_path) -> None:
    from standards_control_plane.evaluators.architecture import _read_repo_file

    (tmp_path / "module.py").write_text("import requests\n", encoding="utf-8")

    assert _read_repo_file("module.py", repo_root=tmp_path) == "import requests\n"
    assert _read_repo_file("../outside.py", repo_root=tmp_path) == ""


def test_build_audit_result_reads_scope_from_external_repo_root(tmp_path) -> None:
    external = tmp_path / "adopter"
    (external / "services" / "enrichment").mkdir(parents=True)
    (external / "services" / "enrichment" / "pipeline.py").write_text(
        "VERSION = 1\n", encoding="utf-8"
    )
    request = {
        "mode": "audit",
        "domains": ["architecture"],
        "scope": {
            "paths": ["services/enrichment/pipeline.py"],
            "subsystem": "mapp-pim",
            "area_id": "enrichment",
        },
        "standards_version": "2026-04-12",
    }

    result = build_audit_result(request, repo_root=external)

    assert result["scope"]["area_id"] == "enrichment"
    assert result["domain_status"]["architecture"]["status"] == "evaluated"


def test_architecture_evaluator_returns_seeded_returns_findings() -> None:
    project_area = _returns_area()
    first = evaluate_architecture(project_area, standards_version="2026-04-11")
    second = evaluate_architecture(project_area, standards_version="2026-04-11")
    assert first == second
    assert [finding["rule_id"] for finding in first["findings"]] == [
        "ARCH-001",
        "ARCH-002",
        "ARCH-003",
    ]
    assert first["score"] == 25


def test_is_remote_client_wrapper_matches_naming_convention_only() -> None:
    from standards_control_plane.evaluators.architecture import _is_remote_client_wrapper

    assert _is_remote_client_wrapper("services/enrichment/services/product_core_client.py")
    assert _is_remote_client_wrapper("frontend/lib/api-client.ts")
    assert _is_remote_client_wrapper("services\\enrichment\\Product_Core_Client.PY")
    assert not _is_remote_client_wrapper("services/enrichment/services/client.py")
    assert not _is_remote_client_wrapper("services/enrichment/services/my_client_utils.py")
    assert not _is_remote_client_wrapper("frontend/app/orders/page.tsx")


def test_arch_003_exempts_client_wrapper_but_still_flags_sibling_feature_file(tmp_path) -> None:
    external = tmp_path / "adopter"
    module_dir = external / "services" / "enrichment" / "services"
    module_dir.mkdir(parents=True)
    (module_dir / "product_core_client.py").write_text(
        "import httpx\n\n\ndef make_client():\n    return httpx.AsyncClient()\n",
        encoding="utf-8",
    )
    (module_dir / "feature_view.py").write_text(
        "import httpx\n\n\ndef load():\n    return httpx.get('https://example.test')\n",
        encoding="utf-8",
    )
    (module_dir / "search-client.ts").write_text(
        "export const search = (q: string) => fetch(`/api/search?q=${q}`)\n",
        encoding="utf-8",
    )
    request = {
        "mode": "audit",
        "domains": ["architecture"],
        "scope": {
            "paths": [
                "services/enrichment/services/product_core_client.py",
                "services/enrichment/services/feature_view.py",
                "services/enrichment/services/search-client.ts",
            ],
            "subsystem": "mapp-pim",
            "area_id": "mapp-pim-services",
        },
        "standards_version": "2026-04-12",
    }

    result = build_audit_result(request, repo_root=external)

    arch_003 = [
        finding for finding in result["findings"] if finding["rule_id"] == "ARCH-003"
    ]
    assert len(arch_003) == 1
    flagged_paths = [item["path"] for item in arch_003[0]["evidence"]]
    assert flagged_paths == ["services/enrichment/services/feature_view.py"]
    assert "product_core_client.py" not in arch_003[0]["summary"]


def test_architecture_evaluator_flags_arch_003_from_repo_backed_fixture() -> None:
    project_area = _api_drift_area()
    result = evaluate_architecture(project_area, standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == ["ARCH-003"]
    assert result["findings"][0]["confidence_class"] == "medium"
    assert result["findings"][0]["evidence"][0]["evidence_class"] == "direct_file"
    assert result["score"] == 85


def test_architecture_evaluator_flags_arch_004_from_repo_backed_fixture() -> None:
    project_area = _async_drift_area()
    result = evaluate_architecture(project_area, standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == ["ARCH-004"]
    assert result["findings"][0]["confidence_class"] == "medium"
    assert result["findings"][0]["evidence"][0]["evidence_class"] == "direct_file"
    assert result["score"] == 85


def test_architecture_evaluator_preserves_findings_order() -> None:
    project_area = copy.deepcopy(_returns_area())
    result = evaluate_architecture(project_area, standards_version="2026-04-11")
    assert [finding["finding_id"] for finding in result["findings"]] == [
        "F-ARCH-001-returns-exceptions",
        "F-ARCH-002-returns-exceptions",
        "F-ARCH-003-returns-exceptions",
    ]


def test_audit_builder_preserves_merged_findings_order_with_multiple_evaluated_domains() -> None:
    request = {
        "mode": "audit",
        "domains": ["governance", "architecture", "product"],
        "scope": {
            "paths": ["fixtures/product-drift-console"],
            "subsystem": "ops",
        },
        "standards_version": "2026-04-11",
    }
    result = build_audit_result(request)
    assert result["domain_status"] == {
        "architecture": {"status": "evaluated"},
        "governance": {"status": "evaluated"},
        "product": {"status": "evaluated"},
    }
    assert [finding["rule_id"] for finding in result["findings"]] == [
        "GOV-003",
        "PROD-001",
        "PROD-002",
        "PROD-003",
    ]
