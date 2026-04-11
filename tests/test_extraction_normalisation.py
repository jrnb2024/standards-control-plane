from __future__ import annotations

from pathlib import Path

import pytest

from standards_control_plane.extractor import extract_scope
from standards_control_plane.normaliser import normalise_project_area
from standards_control_plane.resources import examples_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema


def test_extract_scope_returns_expected_canonical_paths() -> None:
    extracted = extract_scope(["fixtures/returns-pilot"])
    assert extracted["scope_paths"] == ["fixtures/returns-pilot"]
    assert [entry["path"] for entry in extracted["files"]] == [
        "fixtures/returns-pilot/backend/services/returns_exception_service.py",
        "fixtures/returns-pilot/docs/enhancements/ENH-042-returns-exceptions.md",
        "fixtures/returns-pilot/docs/reviews/WP-RET-014/review_findings.md",
        "fixtures/returns-pilot/frontend/app/exceptions/page.tsx",
        "fixtures/returns-pilot/frontend/app/shared/filters.ts",
        "fixtures/returns-pilot/frontend/components/ExceptionDetailPanel.tsx",
        "fixtures/returns-pilot/package.json",
        "fixtures/returns-pilot/prompts/returns-exceptions.md",
        "fixtures/returns-pilot/tests/test_returns_exceptions.py",
    ]
    assert extracted == extract_scope(["fixtures/returns-pilot"])


def test_extract_scope_missing_path_fails() -> None:
    with pytest.raises(FileNotFoundError, match="missing-scope"):
        extract_scope(["missing-scope"])


def test_extract_scope_rejects_boundary_escape() -> None:
    with pytest.raises(ValueError, match="escapes repo boundary"):
        extract_scope(["../"])


def test_extract_scope_rejects_symlink_led_escape(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    nested = repo_root / "nested"
    nested.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (nested / "escape.txt").symlink_to(outside)

    with pytest.raises(ValueError, match="Symlinked files are not supported"):
        extract_scope(["nested"], repo_root=repo_root)


def test_extract_scope_rejects_symlink_to_repo_local_target_outside_requested_subtree(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    scoped = repo_root / "scoped"
    scoped.mkdir(parents=True)
    other = repo_root / "other"
    other.mkdir(parents=True)
    outside_scope_file = other / "shared.py"
    outside_scope_file.write_text("value = 1\n", encoding="utf-8")
    (scoped / "linked.py").symlink_to(outside_scope_file)

    with pytest.raises(ValueError, match="Symlinked files are not supported"):
        extract_scope(["scoped"], repo_root=repo_root)


def test_extract_scope_rejects_scope_path_symlink(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    target = repo_root / "real"
    target.mkdir()
    (target / "file.py").write_text("value = 1\n", encoding="utf-8")
    (repo_root / "linked-scope").symlink_to(target, target_is_directory=True)

    with pytest.raises(ValueError, match="unsupported symlink ancestor|Scope path symlinks are not supported"):
        extract_scope(["linked-scope"], repo_root=repo_root)


def test_extract_scope_rejects_symlinked_ancestor_in_requested_path(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    target = repo_root / "real"
    (target / "subdir").mkdir(parents=True)
    ((target / "subdir") / "file.py").write_text("value = 1\n", encoding="utf-8")
    (repo_root / "linked").symlink_to(target, target_is_directory=True)

    with pytest.raises(ValueError, match="unsupported symlink ancestor"):
        extract_scope(["linked/subdir"], repo_root=repo_root)


def test_normalise_project_area_matches_expected_buckets() -> None:
    extracted = extract_scope(["fixtures/returns-pilot"])
    area = normalise_project_area(extracted, subsystem="returns")
    validate_with_schema(area, "project-area.schema.json")
    assert area["area_id"] == "returns-exceptions"
    assert area["artefacts"]["enhancement_specs"] == [
        "fixtures/returns-pilot/docs/enhancements/ENH-042-returns-exceptions.md"
    ]
    assert area["artefacts"]["docs"] == [
        "fixtures/returns-pilot/docs/enhancements/ENH-042-returns-exceptions.md",
        "fixtures/returns-pilot/docs/reviews/WP-RET-014/review_findings.md",
        "fixtures/returns-pilot/prompts/returns-exceptions.md",
    ]
    assert area["artefacts"]["code_paths"] == [
        "fixtures/returns-pilot/backend/services/returns_exception_service.py",
        "fixtures/returns-pilot/frontend/app/exceptions/page.tsx",
        "fixtures/returns-pilot/frontend/app/shared/filters.ts",
        "fixtures/returns-pilot/frontend/components/ExceptionDetailPanel.tsx",
    ]
    assert area["artefacts"]["prompts"] == [
        "fixtures/returns-pilot/prompts/returns-exceptions.md"
    ]
    assert area["artefacts"]["services"] == [
        "fixtures/returns-pilot/backend/services/returns_exception_service.py"
    ]
    assert area["artefacts"]["tests"] == [
        "fixtures/returns-pilot/tests/test_returns_exceptions.py"
    ]
    assert area["artefacts"]["configs"] == [
        "fixtures/returns-pilot/package.json"
    ]
    assert area["artefacts"]["ui_components"] == [
        "fixtures/returns-pilot/frontend/app/exceptions/page.tsx",
        "fixtures/returns-pilot/frontend/components/ExceptionDetailPanel.tsx",
    ]
    assert area["metadata"]["languages"] == ["json", "markdown", "python", "typescript"]
    assert area["metadata"]["frameworks"] == ["react"]


def test_normalise_fails_without_area_hint_when_no_supported_rule_matches(tmp_path: Path) -> None:
    payload = {
        "scope_paths": ["fixtures/example"],
        "files": [
            {
                "path": "fixtures/example/backend/tasks/job.py",
                "extension": ".py",
                "source_scope_path": "fixtures/example",
            }
        ],
    }
    validate_with_schema(payload, "extracted-scope.schema.json")
    with pytest.raises(ValueError, match="Unable to infer area_id"):
        normalise_project_area(payload, subsystem="returns")

    area = normalise_project_area(payload, subsystem="returns", area_hint="returns-jobs")
    assert area["area_id"] == "returns-jobs"


def test_example_project_area_payload_matches_live_output() -> None:
    extracted = extract_scope(["fixtures/returns-pilot"])
    validate_with_schema(extracted, "extracted-scope.schema.json")
    expected_extracted = load_json_file(examples_dir() / "extracted-scope-returns-pilot.json")
    expected_area = load_json_file(examples_dir() / "project-area-returns-exceptions.json")
    assert extracted == expected_extracted
    assert normalise_project_area(extracted, subsystem="returns") == expected_area
