"""Project-area normalisation from extracted scope records."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from .schema_tools import validate_with_schema

CONFIG_FILENAMES = {
    "package.json",
    "tsconfig.json",
    "pyproject.toml",
    "vite.config.ts",
    "vite.config.js",
}

LANGUAGE_BY_EXTENSION = {
    ".dot": "dot",
    ".json": "json",
    ".md": "markdown",
    ".mdx": "markdown",
    ".mmd": "mermaid",
    ".mermaid": "mermaid",
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
}

AREA_SPEC_PATTERN = re.compile(r"ENH-\d+-([a-z0-9-]+)\.md$", re.IGNORECASE)


def _dedupe_sorted(values: list[str]) -> list[str]:
    return sorted(set(values))


def _artifact_buckets() -> dict[str, list[str]]:
    return {
        "docs": [],
        "code_paths": [],
        "enhancement_specs": [],
        "review_evidence": [],
        "prompts": [],
        "ui_components": [],
        "services": [],
        "tests": [],
        "configs": [],
        "storybook_metadata": [],
        "screenshots": [],
        "graphs": [],
    }


def _path_name(path_value: str) -> str:
    return PurePosixPath(path_value.replace("\\", "/")).name


def _is_docs(path_value: str) -> bool:
    path = path_value.replace("\\", "/")
    return (
        path.startswith("docs/")
        or path.startswith("prompts/")
        or "/docs/" in path
        or "/prompts/" in path
    )


def _is_enhancement_spec(path_value: str) -> bool:
    path = path_value.replace("\\", "/")
    return (
        path.startswith("docs/enhancements/")
        or "/docs/enhancements/" in path
        or AREA_SPEC_PATTERN.search(_path_name(path)) is not None
    )


def _is_prompt(path_value: str) -> bool:
    path = path_value.replace("\\", "/")
    return path.startswith("prompts/") or "/prompts/" in path


def _is_review_evidence(path_value: str) -> bool:
    path = path_value.replace("\\", "/")
    return path.startswith("docs/reviews/") or "/docs/reviews/" in path


def _is_test(path_value: str) -> bool:
    lower_name = _path_name(path_value).lower()
    path = path_value.replace("\\", "/")
    return (
        path.startswith("tests/")
        or "/tests/" in path
        or lower_name.startswith("test_")
        or ".test." in lower_name
    )


def _is_config(path_value: str) -> bool:
    lower_name = _path_name(path_value).lower()
    return lower_name in CONFIG_FILENAMES or ".config." in lower_name


def _is_storybook_metadata(path_value: str) -> bool:
    lower_path = path_value.replace("\\", "/").lower()
    lower_name = _path_name(lower_path)
    return (
        lower_path.startswith(".storybook/")
        or lower_path.startswith("storybook/")
        or "/.storybook/" in lower_path
        or "/storybook/" in lower_path
        or ".stories." in lower_name
        or ".story." in lower_name
    )


def _is_screenshot_artifact(path_value: str) -> bool:
    lower_path = path_value.replace("\\", "/").lower()
    lower_name = _path_name(lower_path)
    return (
        lower_path.startswith("screenshots/")
        or lower_path.startswith("__screenshots__/")
        or "/screenshots/" in lower_path
        or "/__screenshots__/" in lower_path
        or "screenshot" in lower_name
    ) and lower_path.endswith((".png", ".jpg", ".jpeg", ".webp"))


def _is_graph_artifact(path_value: str) -> bool:
    lower_path = path_value.replace("\\", "/").lower()
    return (
        lower_path.endswith((".mmd", ".mermaid", ".dot"))
        or lower_path.startswith("graphs/")
        or "/graphs/" in lower_path
    )


def _is_service(path_value: str) -> bool:
    lower_name = _path_name(path_value).lower()
    path = path_value.replace("\\", "/")
    return (
        path.startswith("backend/services/")
        or "/backend/services/" in path
        or "service" in lower_name
        or "action" in lower_name
    )


def _is_code_path(path_value: str) -> bool:
    return path_value.endswith((".py", ".ts", ".tsx", ".js", ".jsx")) and not _is_test(path_value)


def _is_ui_component(path_value: str) -> bool:
    path = path_value.replace("\\", "/")
    return path.endswith((".tsx", ".jsx")) and (
        path.startswith("components/")
        or "/components/" in path
        or path.endswith("/page.tsx")
        or path.endswith("/page.jsx")
    )


def _infer_area_id(paths: list[str], subsystem: str, area_hint: str | None) -> str:
    if area_hint is not None:
        return area_hint

    for path_value in paths:
        match = AREA_SPEC_PATTERN.search(PurePosixPath(path_value).name)
        if match:
            return match.group(1)

    for path_value in paths:
        marker = "/frontend/app/"
        if marker in path_value:
            suffix = path_value.split(marker, maxsplit=1)[1]
            suffix_path = PurePosixPath(suffix)
            if suffix_path.name in {"page.tsx", "page.jsx"} and len(suffix_path.parts) >= 2:
                route_segment = suffix_path.parts[0]
                return f"{subsystem}-{route_segment}"

    raise ValueError("Unable to infer area_id from extracted scope; explicit area_hint required")


def normalise_project_area(
    extracted_scope: dict[str, Any],
    subsystem: str,
    area_hint: str | None = None,
) -> dict[str, Any]:
    validate_with_schema(extracted_scope, "extracted-scope.schema.json")

    files = extracted_scope["files"]
    assert isinstance(files, list)
    paths = [str(entry["path"]) for entry in files]

    artefacts = _artifact_buckets()
    languages: list[str] = []
    frameworks: list[str] = []
    tags: list[str] = [subsystem]

    for entry in files:
        path_value = str(entry["path"])
        extension = str(entry["extension"])
        if _is_docs(path_value):
            artefacts["docs"].append(path_value)
        if _is_code_path(path_value):
            artefacts["code_paths"].append(path_value)
        if _is_enhancement_spec(path_value):
            artefacts["enhancement_specs"].append(path_value)
        if _is_review_evidence(path_value):
            artefacts["review_evidence"].append(path_value)
        if _is_prompt(path_value):
            artefacts["prompts"].append(path_value)
        if _is_ui_component(path_value):
            artefacts["ui_components"].append(path_value)
        if _is_service(path_value):
            artefacts["services"].append(path_value)
        if _is_test(path_value):
            artefacts["tests"].append(path_value)
        if _is_config(path_value):
            artefacts["configs"].append(path_value)
        if _is_storybook_metadata(path_value):
            artefacts["storybook_metadata"].append(path_value)
        if _is_screenshot_artifact(path_value):
            artefacts["screenshots"].append(path_value)
        if _is_graph_artifact(path_value):
            artefacts["graphs"].append(path_value)

        language = LANGUAGE_BY_EXTENSION.get(extension)
        if language is not None:
            languages.append(language)
        if (
            path_value.startswith("frontend/")
            or path_value.startswith("components/")
            or "/frontend/" in path_value
            or "/components/" in path_value
        ):
            frameworks.append("react")
            tags.append("frontend")
        if _is_storybook_metadata(path_value):
            tags.append("storybook")
        if _is_screenshot_artifact(path_value):
            tags.append("screenshots")
        if _is_graph_artifact(path_value):
            tags.append("graphs")
        if path_value.startswith("backend/") or "/backend/" in path_value:
            tags.append("backend")
        if path_value.startswith("docs/") or "/docs/" in path_value:
            tags.append("docs")

    area_id = _infer_area_id(paths, subsystem=subsystem, area_hint=area_hint)
    tags.extend(area_id.split("-"))
    tags.append(area_id)

    payload = {
        "area_id": area_id,
        "paths": sorted(paths),
        "subsystem": subsystem,
        "artefacts": {
            name: _dedupe_sorted(values)
            for name, values in artefacts.items()
        },
        "metadata": {
            "languages": _dedupe_sorted(languages),
            "frameworks": _dedupe_sorted(frameworks),
            "tags": _dedupe_sorted(tags),
        },
    }
    validate_with_schema(payload, "project-area.schema.json")
    return payload
