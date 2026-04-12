from __future__ import annotations

import json
from pathlib import Path

from standards_control_plane.resources import standards_dir


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_top_level_registry_references_existing_domain_indexes() -> None:
    registry = _load_json(standards_dir() / "standards-index.json")
    domains = registry["domains"]
    assert isinstance(domains, dict)
    for relative_path in domains.values():
        assert isinstance(relative_path, str)
        assert (standards_dir() / relative_path).exists()


def test_domain_indexes_reference_existing_files() -> None:
    for index_path in [
        standards_dir() / "governance" / "index.json",
        standards_dir() / "architecture" / "index.json",
        standards_dir() / "ux" / "index.json",
        standards_dir() / "design" / "index.json",
    ]:
        index_data = _load_json(index_path)
        base_dir = index_path.parent
        for collection_name in ["rules", "patterns"]:
            entries = index_data.get(collection_name, [])
            assert isinstance(entries, list)
            for entry in entries:
                assert isinstance(entry, dict)
                relative_path = entry["path"]
                assert isinstance(relative_path, str)
                assert (base_dir / relative_path).exists()
