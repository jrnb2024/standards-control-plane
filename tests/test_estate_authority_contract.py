from __future__ import annotations

import base64
import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from standards_control_plane import estate_authority
from standards_control_plane.estate_authority import (
    EstateAuthorityError,
    canonical_json_bytes,
    serialize_authority_high_water,
    sha256_digest,
    validate_authority_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas" / "estate-authority" / "v1"
FIXTURE_ROOT = ROOT / "fixtures" / "estate-authority" / "v1"
NOW = datetime(2026, 9, 1, 21, 0, tzinfo=UTC)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_validator() -> Draft202012Validator:
    registry_schema = _load_json(SCHEMA_ROOT / "authority-registry.schema.json")
    bundle_schema = _load_json(SCHEMA_ROOT / "authority-bundle.schema.json")
    registry = Registry().with_resource(
        registry_schema["$id"], Resource.from_contents(registry_schema)
    )
    return Draft202012Validator(bundle_schema, registry=registry)


def _public_pem(private_key: Ed25519PrivateKey) -> str:
    return private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


def _signature(private_key: Ed25519PrivateKey, schema_version: str, payload: object) -> str:
    value = private_key.sign(
        canonical_json_bytes({"schema_version": schema_version, "payload": payload})
    )
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _envelope(
    private_key: Ed25519PrivateKey,
    key_id: str,
    schema_version: str,
    payload: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "payload": payload,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": key_id,
            "value": _signature(private_key, schema_version, payload),
        },
    }


def _build_bundle(
    *,
    authority_epoch: int = 1,
    sequence: int = 1,
    predecessor_digest: str | None = None,
    include_second: bool = False,
    revoke_second: bool = False,
) -> tuple[dict[str, object], dict[str, object]]:
    root_key = Ed25519PrivateKey.generate()
    selector_key = Ed25519PrivateKey.generate()
    issued_at = "2026-09-01T20:59:00Z"
    head_expiry = "2026-09-01T22:00:00Z"
    selection_expiry = "2026-09-02T21:00:00Z"
    registry_payload: dict[str, object] = {
        "registry_id": "scp-estate-authority",
        "registry_epoch": 1,
        "sequence": 1,
        "predecessor_digest": None,
        "issued_at": "2026-09-01T20:00:00Z",
        "expires_at": "2026-09-02T20:00:00Z",
        "keys": [
            {
                "key_id": "scp-registry-root-1",
                "purpose": "estate-authority-registry-root",
                "status": "active",
                "public_key_pem": _public_pem(root_key),
                "not_before": "2026-09-01T00:00:00Z",
                "not_after": "2026-09-03T00:00:00Z",
            },
            {
                "key_id": "scp-selector-1",
                "purpose": "estate-document-authority-selection",
                "status": "active",
                "public_key_pem": _public_pem(selector_key),
                "not_before": "2026-09-01T00:00:00Z",
                "not_after": "2026-09-03T00:00:00Z",
            },
        ],
        "rotation": None,
    }
    registry = _envelope(
        root_key,
        "scp-registry-root-1",
        "estate-authority-selector-registry/v1",
        registry_payload,
    )
    registry_digest = sha256_digest(canonical_json_bytes(registry))

    def selection_payload(
        selection_id: str, path: str, lifecycle: str, authority: str
    ) -> dict[str, object]:
        return {
            "selection_id": selection_id,
            "project_id": "doc-agent",
            "repository_id": "mapp-doc-agent",
            "source_revision": "a" * 40,
            "path": path,
            "source_blob_sha256": "b" * 64,
            "lifecycle": lifecycle,
            "authority": authority,
            "evidence_scope": "repository_guidance",
            "selector_id": "scp-selector-1",
            "sequence": sequence,
            "predecessor_digest": predecessor_digest,
            "review_ref": "DA-ESTATE-CONTEXT-CLOSURE-001",
            "expires_at": selection_expiry,
            "supersedes": [],
        }

    selections = [
        _envelope(
            selector_key,
            "scp-selector-1",
            "estate-authority-selection/v1",
            selection_payload("selection-guidance", "CLAUDE.md", "canonical", "canonical"),
        )
    ]
    if include_second:
        selections.append(
            _envelope(
                selector_key,
                "scp-selector-1",
                "estate-authority-selection/v1",
                selection_payload(
                    "selection-history",
                    "docs/old-topology.md",
                    "superseded",
                    "superseded",
                ),
            )
        )
    selection_envelopes = sorted(
        selections,
        key=lambda row: (
            row["payload"]["repository_id"],
            row["payload"]["path"],
            row["payload"]["selection_id"],
        ),
    )
    selection_envelopes_digest = sha256_digest(
        canonical_json_bytes({"selections": selection_envelopes})
    )
    revoked_selection_digests = []
    if revoke_second:
        revoked_selection_digests = [sha256_digest(canonical_json_bytes(selections[1]))]
    revocations = {
        "revoked_key_ids": [],
        "revoked_selection_digests": revoked_selection_digests,
    }
    revocation_digest = sha256_digest(canonical_json_bytes(revocations))
    head_payload: dict[str, object] = {
        "authority_epoch": authority_epoch,
        "sequence": sequence,
        "head_digest": "sha256:" + ("0" * 64),
        "predecessor_digest": predecessor_digest,
        "selector_registry_digest": registry_digest,
        "selection_envelopes_digest": selection_envelopes_digest,
        "selection_digest": "sha256:" + ("0" * 64),
        "revocation_digest": revocation_digest,
        "active_key_ids": ["scp-selector-1"],
        "revoked_key_ids": [],
        "revoked_selection_digests": revoked_selection_digests,
        "issued_at": issued_at,
        "expires_at": head_expiry,
        "review_ref": "DA-ESTATE-CONTEXT-CLOSURE-001",
        "epoch_transition": None,
    }
    head_core = {
        key: value
        for key, value in head_payload.items()
        if key not in {"head_digest", "selection_digest"}
    }
    head_payload["head_digest"] = sha256_digest(canonical_json_bytes(head_core))
    revoked = set(revoked_selection_digests)
    rows = [
        row["payload"]
        for row in selection_envelopes
        if sha256_digest(canonical_json_bytes(row)) not in revoked
    ]
    projection = {
        "schema_version": "estate-authority-selections/v1",
        "authority_epoch": authority_epoch,
        "sequence": sequence,
        "head_digest": head_payload["head_digest"],
        "selections": rows,
    }
    head_payload["selection_digest"] = sha256_digest(canonical_json_bytes(projection))
    head = _envelope(
        selector_key, "scp-selector-1", "estate-authority-head/v1", head_payload
    )
    return (
        {
            "schema_version": "estate-authority-bundle/v1",
            "registry": registry,
            "head": head,
            "selections": selections,
        },
        {
            "registry_digest": registry_digest,
            "head_digest": head_payload["head_digest"],
            "selection_digest": head_payload["selection_digest"],
            "root_key": root_key,
            "selector_key": selector_key,
        },
    )


def _resign_selection(
    bundle: dict[str, object], identities: dict[str, object], index: int
) -> None:
    selection = bundle["selections"][index]
    selection["signature"]["value"] = _signature(
        identities["selector_key"], selection["schema_version"], selection["payload"]
    )


def _refresh_bundle(
    bundle: dict[str, object],
    identities: dict[str, object],
    *,
    registry_key: Ed25519PrivateKey | None = None,
) -> None:
    registry = bundle["registry"]
    if registry_key is not None:
        registry["signature"]["value"] = _signature(
            registry_key, registry["schema_version"], registry["payload"]
        )
    registry_digest = sha256_digest(canonical_json_bytes(registry))
    identities["registry_digest"] = registry_digest
    head = bundle["head"]
    head_payload = head["payload"]
    head_payload["selector_registry_digest"] = registry_digest
    selection_envelopes = sorted(
        bundle["selections"],
        key=lambda row: (
            row["payload"]["repository_id"],
            row["payload"]["path"],
            row["payload"]["selection_id"],
        ),
    )
    head_payload["selection_envelopes_digest"] = sha256_digest(
        canonical_json_bytes({"selections": selection_envelopes})
    )
    revocations = {
        "revoked_key_ids": head_payload["revoked_key_ids"],
        "revoked_selection_digests": head_payload["revoked_selection_digests"],
    }
    head_payload["revocation_digest"] = sha256_digest(canonical_json_bytes(revocations))
    head_payload["head_digest"] = sha256_digest(
        canonical_json_bytes(
            {
                key: value
                for key, value in head_payload.items()
                if key not in {"head_digest", "selection_digest"}
            }
        )
    )
    revoked = set(head_payload["revoked_selection_digests"])
    projection = {
        "schema_version": "estate-authority-selections/v1",
        "authority_epoch": head_payload["authority_epoch"],
        "sequence": head_payload["sequence"],
        "head_digest": head_payload["head_digest"],
        "selections": [
            row["payload"]
            for row in selection_envelopes
            if sha256_digest(canonical_json_bytes(row)) not in revoked
        ],
    }
    head_payload["selection_digest"] = sha256_digest(canonical_json_bytes(projection))
    head["signature"]["value"] = _signature(
        identities["selector_key"], head["schema_version"], head_payload
    )
    identities["head_digest"] = head_payload["head_digest"]
    identities["selection_digest"] = head_payload["selection_digest"]


def _rotate_registry(
    bundle: dict[str, object], identities: dict[str, object]
) -> Ed25519PrivateKey:
    old_root = identities["root_key"]
    new_root = Ed25519PrivateKey.generate()
    registry = bundle["registry"]
    prior_digest = identities["registry_digest"]
    old_row = registry["payload"]["keys"][0]
    old_row["status"] = "revoked"
    registry["payload"]["keys"].append(
        {
            "key_id": "scp-registry-root-2",
            "purpose": "estate-authority-registry-root",
            "status": "active",
            "public_key_pem": _public_pem(new_root),
            "not_before": "2026-09-01T00:00:00Z",
            "not_after": "2026-09-03T00:00:00Z",
        }
    )
    registry["payload"]["sequence"] = 2
    registry["payload"]["predecessor_digest"] = prior_digest
    rotation = {
        "prior_registry_digest": prior_digest,
        "prior_key_id": "scp-registry-root-1",
        "introduced_key_id": "scp-registry-root-2",
        "prior_signature": "A" * 86,
        "introduced_signature": "A" * 86,
    }
    registry["payload"]["rotation"] = rotation
    rotation_payload = copy.deepcopy(registry["payload"])
    rotation_payload["rotation"] = {
        key: value
        for key, value in rotation.items()
        if key not in {"prior_signature", "introduced_signature"}
    }
    signed = {
        "schema_version": "estate-authority-registry-rotation/v1",
        "payload": rotation_payload,
    }
    rotation["prior_signature"] = base64.urlsafe_b64encode(
        old_root.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    rotation["introduced_signature"] = base64.urlsafe_b64encode(
        new_root.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    registry["signature"]["key_id"] = "scp-registry-root-2"
    _refresh_bundle(bundle, identities, registry_key=new_root)
    return new_root


def _state(previous: dict[str, object]) -> dict[str, object]:
    if previous.get("schema_version") == "estate-authority-high-water/v1":
        return previous["state"]
    return previous


def _advance_head_for_registry(
    bundle: dict[str, object],
    identities: dict[str, object],
    previous: dict[str, object],
    registry_key: Ed25519PrivateKey,
) -> None:
    prior = _state(previous)
    sequence = prior["sequence"] + 1
    head_payload = bundle["head"]["payload"]
    head_payload["sequence"] = sequence
    head_payload["predecessor_digest"] = prior["head_digest"]
    for index, selection in enumerate(bundle["selections"]):
        selection["payload"]["sequence"] = sequence
        selection["payload"]["predecessor_digest"] = prior["head_digest"]
        _resign_selection(bundle, identities, index)
    _refresh_bundle(bundle, identities, registry_key=registry_key)


def _transition_registry(
    bundle: dict[str, object],
    identities: dict[str, object],
    previous: dict[str, object],
    *,
    prior_key_id: str,
    prior_key: Ed25519PrivateKey,
    introduced_key_id: str,
    introduced_key: Ed25519PrivateKey,
    remove_key_ids: set[str] | None = None,
) -> None:
    registry = bundle["registry"]
    payload = registry["payload"]
    remove = remove_key_ids or set()
    payload["keys"] = [row for row in payload["keys"] if row["key_id"] not in remove]
    if not any(row["key_id"] == introduced_key_id for row in payload["keys"]):
        payload["keys"].append(
            {
                "key_id": introduced_key_id,
                "purpose": "estate-authority-registry-root",
                "status": "active",
                "public_key_pem": _public_pem(introduced_key),
                "not_before": "2026-09-01T00:00:00Z",
                "not_after": "2026-09-03T00:00:00Z",
            }
        )
    prior_digest = identities["registry_digest"]
    payload["sequence"] += 1
    payload["predecessor_digest"] = prior_digest
    rotation = {
        "prior_registry_digest": prior_digest,
        "prior_key_id": prior_key_id,
        "introduced_key_id": introduced_key_id,
        "prior_signature": "A" * 86,
        "introduced_signature": "A" * 86,
    }
    payload["rotation"] = rotation
    rotation_payload = copy.deepcopy(payload)
    rotation_payload["rotation"] = {
        key: value
        for key, value in rotation.items()
        if key not in {"prior_signature", "introduced_signature"}
    }
    signed = {
        "schema_version": "estate-authority-registry-rotation/v1",
        "payload": rotation_payload,
    }
    rotation["prior_signature"] = base64.urlsafe_b64encode(
        prior_key.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    rotation["introduced_signature"] = base64.urlsafe_b64encode(
        introduced_key.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    registry["signature"]["key_id"] = introduced_key_id
    _advance_head_for_registry(bundle, identities, previous, introduced_key)


def _expect_code(bundle: dict[str, object], registry_digest: str, code: str) -> None:
    with pytest.raises(EstateAuthorityError) as caught:
        validate_authority_bundle(
            bundle,
            expected_registry_digest=registry_digest,
            now=NOW,
        )
    assert caught.value.code == code


def _high_water(result: dict[str, object]) -> dict[str, object]:
    fields = {
        "authority_epoch",
        "sequence",
        "head_digest",
        "registry_epoch",
        "registry_sequence",
        "registry_digest",
        "registry_revoked_key_ids",
        "registry_key_bindings",
        "registry_retired_key_ids",
        "registry_retired_public_key_sha256",
        "revoked_selection_digests",
        "selection_envelope_digests",
    }
    return {key: copy.deepcopy(result[key]) for key in fields}


def test_schemas_are_draft_2020_12_closed_and_resolve() -> None:
    Draft202012Validator.check_schema(
        _load_json(SCHEMA_ROOT / "authority-registry.schema.json")
    )
    Draft202012Validator.check_schema(_load_json(SCHEMA_ROOT / "authority-bundle.schema.json"))
    Draft202012Validator.check_schema(
        _load_json(SCHEMA_ROOT / "authority-high-water.schema.json")
    )
    validator = _schema_validator()
    bundle, _ = _build_bundle()
    validator.validate(bundle)

    tampered = copy.deepcopy(bundle)
    tampered["head"]["payload"]["unexpected"] = True
    assert next(validator.iter_errors(tampered)).validator == "additionalProperties"


def test_valid_dynamic_bundle_projects_exact_doc_agent_selection_shape() -> None:
    bundle, identities = _build_bundle()
    result = validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )

    assert result["head_digest"] == identities["head_digest"]
    assert result["selection_digest"] == identities["selection_digest"]
    assert result["projection"] == {
        "schema_version": "estate-authority-selections/v1",
        "authority_epoch": 1,
        "sequence": 1,
        "head_digest": identities["head_digest"],
        "selections": [bundle["selections"][0]["payload"]],
    }
    assert set(result["projection"]["selections"][0]) == {
        "selection_id",
        "project_id",
        "repository_id",
        "source_revision",
        "path",
        "source_blob_sha256",
        "lifecycle",
        "authority",
        "evidence_scope",
        "selector_id",
        "sequence",
        "predecessor_digest",
        "review_ref",
        "expires_at",
        "supersedes",
    }


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda row: row["registry"]["payload"].update({"registry_id": "tampered"}),
            "authority_registry_digest_mismatch",
        ),
        (
            lambda row: row["head"]["payload"].update({"review_ref": "tampered"}),
            "authority_head_digest_mismatch",
        ),
        (
            lambda row: row["selections"][0]["payload"].update({"path": "AGENTS.md"}),
            "authority_selection_signature_invalid",
        ),
        (
            lambda row: row["registry"]["signature"].update({"value": "A" * 86}),
            "authority_registry_digest_mismatch",
        ),
        (
            lambda row: row["head"]["signature"].update({"value": "A" * 86}),
            "authority_head_signature_invalid",
        ),
        (
            lambda row: row["selections"][0]["signature"].update({"value": "A" * 86}),
            "authority_selection_signature_invalid",
        ),
    ],
)
def test_signature_and_payload_tampering_fail_closed(mutation, code: str) -> None:
    bundle, identities = _build_bundle()
    mutation(bundle)
    _expect_code(bundle, identities["registry_digest"], code)


def test_selector_purpose_and_status_are_enforced_before_authority() -> None:
    bundle, identities = _build_bundle()
    selector = bundle["registry"]["payload"]["keys"][1]
    selector["purpose"] = "estate-authority-registry-root"
    _expect_code(bundle, identities["registry_digest"], "authority_registry_digest_mismatch")

    bundle, identities = _build_bundle()
    selector = bundle["registry"]["payload"]["keys"][1]
    selector["status"] = "revoked"
    registry = bundle["registry"]
    identities["registry_digest"] = sha256_digest(canonical_json_bytes(registry))
    _expect_code(bundle, identities["registry_digest"], "authority_registry_signature_invalid")


def test_revoked_selection_is_removed_and_changes_projection_digest() -> None:
    bundle, identities = _build_bundle(include_second=True)
    original_payloads = copy.deepcopy([row["payload"] for row in bundle["selections"]])
    baseline_result = validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    revoked_digest = sha256_digest(canonical_json_bytes(bundle["selections"][1]))
    bundle["head"]["payload"]["revoked_selection_digests"] = [revoked_digest]
    _refresh_bundle(bundle, identities)
    revoked_result = validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )

    assert len(baseline_result["projection"]["selections"]) == 2
    assert len(revoked_result["projection"]["selections"]) == 1
    assert revoked_result["selection_digest"] != baseline_result["selection_digest"]
    assert (
        revoked_result["selection_envelopes_digest"]
        == baseline_result["selection_envelopes_digest"]
    )
    assert revoked_result["registry_digest"] == baseline_result["registry_digest"]
    assert [row["payload"] for row in bundle["selections"]] == original_payloads


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("expires_at", "2026-09-01T20:59:59Z", "authority_head_expired"),
        ("issued_at", "2026-09-01T21:00:06Z", "authority_head_time_invalid"),
    ],
)
def test_head_time_bounds_fail_closed(field: str, value: str, code: str) -> None:
    bundle, identities = _build_bundle()
    bundle["head"]["payload"][field] = value
    _expect_code(bundle, identities["registry_digest"], code)


def test_sequence_rollback_fork_and_predecessor_mismatch_fail() -> None:
    bundle, identities = _build_bundle(sequence=1)
    previous = {
        "authority_epoch": 1,
        "sequence": 2,
        "head_digest": "sha256:" + ("c" * 64),
        "registry_epoch": 1,
        "registry_sequence": 1,
        "registry_digest": identities["registry_digest"],
        "registry_revoked_key_ids": [],
        "revoked_selection_digests": [],
    }
    with pytest.raises(EstateAuthorityError, match="authority_head_rollback"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=previous,
        )

    previous["sequence"] = 1
    with pytest.raises(EstateAuthorityError, match="authority_head_fork"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=previous,
        )

    previous["sequence"] = 1
    previous["head_digest"] = "sha256:" + ("c" * 64)
    bundle, identities = _build_bundle(sequence=2, predecessor_digest=None)
    previous["registry_digest"] = identities["registry_digest"]
    with pytest.raises(EstateAuthorityError, match="authority_head_predecessor_mismatch"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=previous,
        )


def test_invalid_lifecycle_authority_pair_is_rejected() -> None:
    bundle, identities = _build_bundle()
    bundle["selections"][0]["payload"]["authority"] = "active_noncanonical"
    _expect_code(bundle, identities["registry_digest"], "authority_selection_lifecycle_invalid")


def test_registry_signature_is_checked_after_the_pinned_digest() -> None:
    bundle, _ = _build_bundle()
    bundle["registry"]["signature"]["value"] = "A" * 86
    tampered_digest = sha256_digest(canonical_json_bytes(bundle["registry"]))
    _expect_code(bundle, tampered_digest, "authority_registry_signature_invalid")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("purpose", "estate-authority-registry-root"),
        ("status", "revoked"),
    ],
)
def test_selector_key_must_be_active_and_purpose_separated(field: str, value: str) -> None:
    bundle, identities = _build_bundle()
    bundle["registry"]["payload"]["keys"][1][field] = value
    _refresh_bundle(bundle, identities, registry_key=identities["root_key"])
    _expect_code(bundle, identities["registry_digest"], "authority_head_key_rejected")


def test_registry_rotation_requires_old_and_new_root_signatures() -> None:
    bundle, identities = _build_bundle()
    new_root = _rotate_registry(bundle, identities)
    validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    bundle["registry"]["payload"]["rotation"]["prior_signature"] = "A" * 86
    _refresh_bundle(bundle, identities, registry_key=new_root)
    _expect_code(
        bundle,
        identities["registry_digest"],
        "authority_registry_rotation_signature_invalid",
    )


def test_registry_rotation_is_chained_to_the_persisted_registry_high_water() -> None:
    bundle, identities = _build_bundle()
    previous = _high_water(
        validate_authority_bundle(
            copy.deepcopy(bundle),
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
        )
    )
    _rotate_registry(bundle, identities)
    bundle["head"]["payload"]["sequence"] = 2
    bundle["head"]["payload"]["predecessor_digest"] = previous["head_digest"]
    bundle["selections"][0]["payload"]["sequence"] = 2
    bundle["selections"][0]["payload"]["predecessor_digest"] = previous["head_digest"]
    _resign_selection(bundle, identities, 0)
    _refresh_bundle(bundle, identities)
    validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
        previous=previous,
    )

    previous["registry_sequence"] = 2
    with pytest.raises(EstateAuthorityError, match="authority_registry_rollback"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=previous,
        )


def test_revoked_prior_root_cannot_authorize_a_later_registry_transition() -> None:
    bundle, identities = _build_bundle()
    first = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    root_two = _rotate_registry(bundle, identities)
    _advance_head_for_registry(bundle, identities, first["high_water"], root_two)
    second = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
        previous=first["high_water"],
    )

    root_three = Ed25519PrivateKey.generate()
    _transition_registry(
        bundle,
        identities,
        second["high_water"],
        prior_key_id="scp-registry-root-1",
        prior_key=identities["root_key"],
        introduced_key_id="scp-registry-root-3",
        introduced_key=root_three,
    )
    with pytest.raises(
        EstateAuthorityError, match="authority_registry_rotation_prior_rejected"
    ):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=second["high_water"],
        )


def test_expired_prior_binding_cannot_authorize_registry_transition() -> None:
    bundle, identities = _build_bundle()
    bundle["registry"]["payload"]["keys"][0]["not_after"] = (
        "2026-09-01T21:00:30Z"
    )
    _refresh_bundle(bundle, identities, registry_key=identities["root_key"])
    first = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )

    new_root = _rotate_registry(bundle, identities)
    _advance_head_for_registry(bundle, identities, first["high_water"], new_root)
    with pytest.raises(
        EstateAuthorityError, match="authority_registry_rotation_prior_rejected"
    ):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=datetime(2026, 9, 1, 21, 1, tzinfo=UTC),
            previous=first["high_water"],
        )


def test_registry_rotation_requires_a_genuinely_new_introduced_key_id() -> None:
    bundle, identities = _build_bundle()
    root_two = Ed25519PrivateKey.generate()
    bundle["registry"]["payload"]["keys"].append(
        {
            "key_id": "scp-registry-root-2",
            "purpose": "estate-authority-registry-root",
            "status": "active",
            "public_key_pem": _public_pem(root_two),
            "not_before": "2026-09-01T00:00:00Z",
            "not_after": "2026-09-03T00:00:00Z",
        }
    )
    _refresh_bundle(bundle, identities, registry_key=identities["root_key"])
    first = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    _transition_registry(
        bundle,
        identities,
        first["high_water"],
        prior_key_id="scp-registry-root-1",
        prior_key=identities["root_key"],
        introduced_key_id="scp-registry-root-2",
        introduced_key=root_two,
    )
    with pytest.raises(
        EstateAuthorityError, match="authority_registry_rotation_introduced_not_new"
    ):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=first["high_water"],
        )


def test_registry_cannot_resurrect_a_persisted_revoked_key_id() -> None:
    bundle, identities = _build_bundle()
    previous = {
        "authority_epoch": 1,
        "sequence": 1,
        "head_digest": identities["head_digest"],
        "registry_epoch": 1,
        "registry_sequence": 1,
        "registry_digest": identities["registry_digest"],
        "registry_revoked_key_ids": ["scp-registry-root-1"],
        "revoked_selection_digests": [],
    }
    with pytest.raises(EstateAuthorityError, match="authority_registry_key_resurrection"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=previous,
        )


def test_legacy_retired_id_without_material_fingerprint_fails_closed() -> None:
    bundle, identities = _build_bundle()
    previous = {
        "authority_epoch": 1,
        "sequence": 1,
        "head_digest": identities["head_digest"],
        "registry_epoch": 1,
        "registry_sequence": 1,
        "registry_digest": identities["registry_digest"],
        "registry_revoked_key_ids": ["retired-selector-key"],
        "revoked_selection_digests": [],
    }
    with pytest.raises(
        EstateAuthorityError, match="authority_previous_state_upgrade_required"
    ):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=previous,
        )


def test_legacy_state_without_retired_ids_upgrades_on_unchanged_registry() -> None:
    bundle, identities = _build_bundle()
    previous = {
        "authority_epoch": 1,
        "sequence": 1,
        "head_digest": identities["head_digest"],
        "registry_epoch": 1,
        "registry_sequence": 1,
        "registry_digest": identities["registry_digest"],
        "registry_revoked_key_ids": [],
        "revoked_selection_digests": ["sha256:" + ("9" * 64)],
    }
    result = validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
        previous=previous,
    )
    assert result["revoked_selection_digests"] == ["sha256:" + ("9" * 64)]
    assert result["high_water"]["state"]["registry_retired_key_ids"] == []
    assert result["high_water"]["state"]["registry_retired_public_key_sha256"] == []


def test_pre_material_tombstone_state_with_retired_ids_requires_history_migration() -> None:
    bundle, identities = _build_bundle()
    first = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    previous = copy.deepcopy(first["high_water"]["state"])
    previous.pop("registry_retired_public_key_sha256")
    previous["registry_retired_key_ids"] = ["retired-before-material-contract"]
    previous["registry_revoked_key_ids"] = ["retired-before-material-contract"]

    with pytest.raises(
        EstateAuthorityError, match="authority_previous_state_upgrade_required"
    ):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=previous,
        )


def test_revoke_remove_and_retired_key_resurrection_use_real_registry_transitions() -> None:
    bundle, identities = _build_bundle()
    first = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    retired_row = copy.deepcopy(bundle["registry"]["payload"]["keys"][0])
    root_two = _rotate_registry(bundle, identities)
    _advance_head_for_registry(bundle, identities, first["high_water"], root_two)
    second = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
        previous=first["high_water"],
    )

    root_three = Ed25519PrivateKey.generate()
    _transition_registry(
        bundle,
        identities,
        second["high_water"],
        prior_key_id="scp-registry-root-2",
        prior_key=root_two,
        introduced_key_id="scp-registry-root-3",
        introduced_key=root_three,
        remove_key_ids={"scp-registry-root-1"},
    )
    third = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
        previous=second["high_water"],
    )
    assert third["registry_retired_key_ids"] == ["scp-registry-root-1"]
    assert "scp-registry-root-1" in third["registry_revoked_key_ids"]
    retired_fingerprint = estate_authority._public_key_fingerprint(
        identities["root_key"].public_key()
    )
    assert third["registry_retired_public_key_sha256"] == [retired_fingerprint]
    assert third["high_water"]["state"]["registry_retired_public_key_sha256"] == [
        retired_fingerprint
    ]

    persisted = json.loads(serialize_authority_high_water(third["high_water"]))
    material_bundle = copy.deepcopy(bundle)
    material_identities = dict(identities)
    _transition_registry(
        material_bundle,
        material_identities,
        persisted,
        prior_key_id="scp-registry-root-3",
        prior_key=root_three,
        introduced_key_id="scp-registry-root-reborn",
        introduced_key=identities["root_key"],
    )
    with pytest.raises(
        EstateAuthorityError, match="authority_registry_key_material_resurrection"
    ):
        validate_authority_bundle(
            material_bundle,
            expected_registry_digest=material_identities["registry_digest"],
            now=NOW,
            previous=persisted,
        )

    bundle["registry"]["payload"]["keys"].append(retired_row)
    root_four = Ed25519PrivateKey.generate()
    _transition_registry(
        bundle,
        identities,
        third["high_water"],
        prior_key_id="scp-registry-root-3",
        prior_key=root_three,
        introduced_key_id="scp-registry-root-4",
        introduced_key=root_four,
    )
    with pytest.raises(EstateAuthorityError, match="authority_registry_key_resurrection"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=third["high_water"],
        )


def test_removed_key_material_cannot_move_to_fresh_id_in_same_transition() -> None:
    bundle, identities = _build_bundle()
    first = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    root_two = _rotate_registry(bundle, identities)
    _advance_head_for_registry(bundle, identities, first["high_water"], root_two)
    second = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
        previous=first["high_water"],
    )

    _transition_registry(
        bundle,
        identities,
        second["high_water"],
        prior_key_id="scp-registry-root-2",
        prior_key=root_two,
        introduced_key_id="scp-registry-root-reborn",
        introduced_key=identities["root_key"],
        remove_key_ids={"scp-registry-root-1"},
    )
    with pytest.raises(
        EstateAuthorityError, match="authority_registry_key_material_resurrection"
    ):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=second["high_water"],
        )


def test_supersession_near_schema_limit_is_iterative_and_cycles_stay_stable() -> None:
    rows = [
        {
            "selection_id": f"selection-{index}",
            "lifecycle": "superseded",
            "supersedes": [f"selection-{index + 1}"] if index < 9_999 else [],
        }
        for index in range(10_000)
    ]
    estate_authority._validate_supersession(rows)
    rows[-1]["supersedes"] = ["selection-0"]
    with pytest.raises(EstateAuthorityError, match="authority_supersession_cycle"):
        estate_authority._validate_supersession(rows)


def _advance_authority_epoch() -> tuple[
    dict[str, object], dict[str, object], dict[str, object], Ed25519PrivateKey
]:
    bundle, identities = _build_bundle()
    previous = _high_water(
        validate_authority_bundle(
            copy.deepcopy(bundle),
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
        )
    )
    old_root = identities["root_key"]
    new_root = _rotate_registry(bundle, identities)
    head_payload = bundle["head"]["payload"]
    head_payload["authority_epoch"] = 2
    head_payload["predecessor_digest"] = previous["head_digest"]
    bundle["selections"][0]["payload"]["predecessor_digest"] = previous["head_digest"]
    _resign_selection(bundle, identities, 0)
    transition = {
        "previous_authority_epoch": 1,
        "previous_head_digest": previous["head_digest"],
        "previous_registry_digest": previous["registry_digest"],
        "new_authority_epoch": 2,
        "previous_root_key_id": "scp-registry-root-1",
        "new_root_key_id": "scp-registry-root-2",
        "previous_signature": "A" * 86,
        "new_signature": "A" * 86,
    }
    transition_core = {
        key: value
        for key, value in transition.items()
        if key not in {"previous_signature", "new_signature"}
    }
    signed = {
        "schema_version": "estate-authority-epoch-transition/v1",
        "payload": transition_core,
    }
    transition["previous_signature"] = base64.urlsafe_b64encode(
        old_root.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    transition["new_signature"] = base64.urlsafe_b64encode(
        new_root.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    head_payload["epoch_transition"] = transition
    _refresh_bundle(bundle, identities)
    return bundle, identities, previous, new_root


def test_higher_authority_epoch_requires_dual_root_transition() -> None:
    bundle, identities, previous, _ = _advance_authority_epoch()
    result = validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
        previous=previous,
    )
    assert result["authority_epoch"] == 2

    bundle["head"]["payload"]["epoch_transition"]["previous_signature"] = "A" * 86
    _refresh_bundle(bundle, identities)
    with pytest.raises(
        EstateAuthorityError, match="authority_epoch_transition_signature_invalid"
    ):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=previous,
        )


def test_authority_epoch_transition_rejects_root_already_revoked_in_prior_state() -> None:
    bundle, identities = _build_bundle()
    first = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    old_root = identities["root_key"]
    new_root = _rotate_registry(bundle, identities)
    _advance_head_for_registry(bundle, identities, first["high_water"], new_root)
    second = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
        previous=first["high_water"],
    )

    head_payload = bundle["head"]["payload"]
    head_payload["authority_epoch"] = 2
    head_payload["sequence"] = 3
    head_payload["predecessor_digest"] = second["head_digest"]
    bundle["selections"][0]["payload"]["sequence"] = 3
    bundle["selections"][0]["payload"]["predecessor_digest"] = second[
        "head_digest"
    ]
    _resign_selection(bundle, identities, 0)
    transition = {
        "previous_authority_epoch": 1,
        "previous_head_digest": second["head_digest"],
        "previous_registry_digest": second["registry_digest"],
        "new_authority_epoch": 2,
        "previous_root_key_id": "scp-registry-root-1",
        "new_root_key_id": "scp-registry-root-2",
        "previous_signature": "A" * 86,
        "new_signature": "A" * 86,
    }
    transition_core = {
        key: value
        for key, value in transition.items()
        if key not in {"previous_signature", "new_signature"}
    }
    signed = {
        "schema_version": "estate-authority-epoch-transition/v1",
        "payload": transition_core,
    }
    transition["previous_signature"] = base64.urlsafe_b64encode(
        old_root.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    transition["new_signature"] = base64.urlsafe_b64encode(
        new_root.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    head_payload["epoch_transition"] = transition
    _refresh_bundle(bundle, identities)

    with pytest.raises(EstateAuthorityError, match="authority_epoch_transition_invalid"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=second["high_water"],
        )


def test_authority_epoch_transition_roots_must_remain_inside_validity_windows() -> None:
    old_root = Ed25519PrivateKey.generate()
    new_root = Ed25519PrivateKey.generate()
    previous = {
        "authority_epoch": 1,
        "head_digest": "sha256:" + ("a" * 64),
        "registry_digest": "sha256:" + ("b" * 64),
        "registry_key_bindings": [
            {
                "key_id": "root-old",
                "purpose": "estate-authority-registry-root",
                "status": "active",
                "public_key_sha256": estate_authority._public_key_fingerprint(
                    old_root.public_key()
                ),
                "not_before": "2026-09-01T20:00:00Z",
                "not_after": "2026-09-01T21:00:30Z",
            }
        ],
    }
    transition = {
        "previous_authority_epoch": 1,
        "previous_head_digest": previous["head_digest"],
        "previous_registry_digest": previous["registry_digest"],
        "new_authority_epoch": 2,
        "previous_root_key_id": "root-old",
        "new_root_key_id": "root-new",
        "previous_signature": "A" * 86,
        "new_signature": "A" * 86,
    }
    transition_core = {
        key: value
        for key, value in transition.items()
        if key not in {"previous_signature", "new_signature"}
    }
    signed = {
        "schema_version": "estate-authority-epoch-transition/v1",
        "payload": transition_core,
    }
    transition["previous_signature"] = base64.urlsafe_b64encode(
        old_root.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    transition["new_signature"] = base64.urlsafe_b64encode(
        new_root.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    payload = {"authority_epoch": 2, "epoch_transition": transition}
    keys = {
        "root-old": {
            "purpose": "estate-authority-registry-root",
            "status": "revoked",
            "not_before": "2026-09-01T20:00:00Z",
            "not_after": "2026-09-02T20:00:00Z",
        },
        "root-new": {
            "purpose": "estate-authority-registry-root",
            "status": "active",
            "not_before": "2026-09-01T20:00:00Z",
            "not_after": "2026-09-02T20:00:00Z",
        },
    }
    public_keys = {
        "root-old": old_root.public_key(),
        "root-new": new_root.public_key(),
    }
    issued_at = datetime(2026, 9, 1, 21, 0, tzinfo=UTC)
    validation_time = datetime(2026, 9, 1, 21, 1, tzinfo=UTC)

    with pytest.raises(EstateAuthorityError, match="authority_epoch_transition_invalid"):
        estate_authority._validate_epoch_transition(
            payload, previous, keys, public_keys, validation_time, issued_at
        )


def test_lifecycle_pair_is_checked_after_a_valid_selector_signature() -> None:
    bundle, identities = _build_bundle()
    bundle["selections"][0]["payload"]["authority"] = "active_noncanonical"
    _resign_selection(bundle, identities, 0)
    _refresh_bundle(bundle, identities)
    _expect_code(bundle, identities["registry_digest"], "authority_selection_lifecycle_invalid")


def test_expired_selection_fails_after_valid_signature_and_digests() -> None:
    bundle, identities = _build_bundle()
    bundle["selections"][0]["payload"]["expires_at"] = "2026-09-01T20:59:59Z"
    _resign_selection(bundle, identities, 0)
    _refresh_bundle(bundle, identities)
    _expect_code(bundle, identities["registry_digest"], "authority_selection_expired")


def test_duplicate_binding_fails_even_when_both_envelopes_are_valid() -> None:
    bundle, identities = _build_bundle(include_second=True)
    bundle["selections"][1]["payload"]["path"] = "CLAUDE.md"
    _resign_selection(bundle, identities, 1)
    _refresh_bundle(bundle, identities)
    _expect_code(bundle, identities["registry_digest"], "authority_selection_duplicate")


def test_supersession_target_and_cycle_validation() -> None:
    bundle, identities = _build_bundle(include_second=True)
    bundle["selections"][0]["payload"]["supersedes"] = ["selection-history"]
    _resign_selection(bundle, identities, 0)
    _refresh_bundle(bundle, identities)
    validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )

    bundle["selections"][1]["payload"]["supersedes"] = ["selection-history"]
    _resign_selection(bundle, identities, 1)
    _refresh_bundle(bundle, identities)
    _expect_code(bundle, identities["registry_digest"], "authority_supersession_cycle")


def test_revocation_cannot_name_an_unknown_selection_envelope() -> None:
    bundle, identities = _build_bundle()
    bundle["head"]["payload"]["revoked_selection_digests"] = [
        "sha256:" + ("d" * 64)
    ]
    _refresh_bundle(bundle, identities)
    _expect_code(bundle, identities["registry_digest"], "authority_revocation_target_missing")


@pytest.mark.parametrize(
    "path",
    ["../CLAUDE.md", "/CLAUDE.md", "docs//CLAUDE.md", r"docs\CLAUDE.md", "docs/./x.md"],
)
def test_schema_rejects_non_normalized_or_escaping_paths(path: str) -> None:
    bundle, _ = _build_bundle()
    bundle["selections"][0]["payload"]["path"] = path
    errors = list(_schema_validator().iter_errors(bundle))
    assert errors


def test_path_limit_is_utf8_bytes_not_unicode_codepoints() -> None:
    bundle, identities = _build_bundle()
    bundle["selections"][0]["payload"]["path"] = "é" * 300
    _resign_selection(bundle, identities, 0)
    _refresh_bundle(bundle, identities)
    _expect_code(bundle, identities["registry_digest"], "authority_selection_path_invalid")


@pytest.mark.parametrize(
    "registry_digest",
    ["", "sha256:" + ("A" * 64), "f" * 64, "sha256:" + ("f" * 63)],
)
def test_expected_registry_digest_has_one_exact_grammar(registry_digest: str) -> None:
    bundle, _ = _build_bundle()
    _expect_code(bundle, registry_digest, "authority_registry_digest_invalid")


def test_validation_rejects_naive_clock_and_malformed_previous_state() -> None:
    bundle, identities = _build_bundle()
    with pytest.raises(EstateAuthorityError, match="authority_validation_time_invalid"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=datetime(2026, 9, 1, 21, 0),
        )
    with pytest.raises(EstateAuthorityError, match="authority_previous_state_invalid"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous={
                "authority_epoch": 1,
                "sequence": "1",
                "head_digest": identities["head_digest"],
                "registry_epoch": 1,
                "registry_sequence": 1,
                "registry_digest": identities["registry_digest"],
                "registry_revoked_key_ids": [],
            },
        )


def test_versioned_high_water_round_trips_as_exact_restart_input() -> None:
    bundle, identities = _build_bundle()
    first = validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    encoded = serialize_authority_high_water(first["high_water"])
    persisted = json.loads(encoded)

    second = validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
        previous=persisted,
    )
    assert second["high_water"] == first["high_water"]
    assert serialize_authority_high_water(second["high_water"]) == encoded

    persisted["state"]["sequence"] = 2
    with pytest.raises(
        EstateAuthorityError, match="authority_previous_state_digest_mismatch"
    ):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=persisted,
        )


def test_new_revocation_cannot_overflow_returned_high_water() -> None:
    bundle, identities = _build_bundle()
    first = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    previous = copy.deepcopy(first["high_water"])
    previous["state"]["revoked_selection_digests"] = [
        f"sha256:{index:064x}" for index in range(estate_authority.MAX_PERSISTED_TOMBSTONES)
    ]
    previous["state_digest"] = estate_authority._high_water_digest(previous["state"])
    prior_head = previous["state"]["head_digest"]
    envelope_digest = sha256_digest(canonical_json_bytes(bundle["selections"][0]))
    assert envelope_digest not in previous["state"]["revoked_selection_digests"]
    bundle["head"]["payload"]["sequence"] = 2
    bundle["head"]["payload"]["predecessor_digest"] = prior_head
    bundle["head"]["payload"]["revoked_selection_digests"] = [envelope_digest]
    bundle["selections"][0]["payload"]["sequence"] = 2
    bundle["selections"][0]["payload"]["predecessor_digest"] = prior_head
    _resign_selection(bundle, identities, 0)
    _refresh_bundle(bundle, identities)

    with pytest.raises(
        EstateAuthorityError, match="authority_high_water_capacity_exceeded"
    ):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=previous,
        )


def test_maximum_closed_high_water_fits_the_shared_four_mib_limit() -> None:
    binding_ids = [f"binding-{index}".ljust(128, "x") for index in range(8)]
    retired_ids = [
        f"retired-{index:05d}".ljust(128, "x")
        for index in range(estate_authority.MAX_PERSISTED_TOMBSTONES)
    ]
    digests = [
        f"sha256:{index:064x}"
        for index in range(estate_authority.MAX_PERSISTED_TOMBSTONES)
    ]
    state = {
        "authority_epoch": 1,
        "sequence": 1,
        "head_digest": "sha256:" + ("a" * 64),
        "registry_epoch": 1,
        "registry_sequence": 1,
        "registry_digest": "sha256:" + ("b" * 64),
        "registry_revoked_key_ids": retired_ids,
        "registry_key_bindings": [
            {
                "key_id": key_id,
                "purpose": "estate-authority-registry-root",
                "status": "active",
                "public_key_sha256": f"sha256:{index + 10_000:064x}",
                "not_before": "2026-09-01T00:00:00Z",
                "not_after": "2026-09-03T00:00:00Z",
            }
            for index, key_id in enumerate(binding_ids)
        ],
        "registry_retired_key_ids": retired_ids,
        "registry_retired_public_key_sha256": [
            f"sha256:{index + 20_000:064x}" for index in range(len(retired_ids))
        ],
        "revoked_selection_digests": digests,
        "selection_envelope_digests": digests,
    }
    envelope = estate_authority._build_high_water(state)
    encoded = serialize_authority_high_water(envelope)
    assert len(encoded) > 3 * 1024 * 1024
    assert len(encoded) <= estate_authority.MAX_HIGH_WATER_BYTES


def test_head_must_fit_inside_the_signed_registry_window() -> None:
    bundle, identities = _build_bundle()
    bundle["head"]["payload"]["expires_at"] = "2026-09-02T20:30:00Z"
    _refresh_bundle(bundle, identities)
    _expect_code(
        bundle,
        identities["registry_digest"],
        "authority_head_registry_window_invalid",
    )


def test_projected_selection_file_respects_doc_agent_four_mib_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, identities = _build_bundle()
    monkeypatch.setattr(estate_authority, "MAX_PROJECTED_BYTES", 64)
    _expect_code(bundle, identities["registry_digest"], "authority_projection_too_large")


def test_selection_sequence_and_predecessor_must_match_the_head() -> None:
    bundle, identities = _build_bundle()
    bundle["selections"][0]["payload"]["sequence"] = 2
    _resign_selection(bundle, identities, 0)
    _refresh_bundle(bundle, identities)
    _expect_code(bundle, identities["registry_digest"], "authority_selection_sequence_mismatch")


def test_registry_transition_cannot_replace_key_material_under_an_existing_id() -> None:
    bundle, identities = _build_bundle()
    previous = _high_water(
        validate_authority_bundle(
            copy.deepcopy(bundle),
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
        )
    )
    new_root = _rotate_registry(bundle, identities)
    attacker = Ed25519PrivateKey.generate()
    registry_payload = bundle["registry"]["payload"]
    registry_payload["keys"][0]["public_key_pem"] = _public_pem(attacker)
    rotation = registry_payload["rotation"]
    rotation_payload = copy.deepcopy(registry_payload)
    rotation_payload["rotation"] = {
        key: value
        for key, value in rotation.items()
        if key not in {"prior_signature", "introduced_signature"}
    }
    signed = {
        "schema_version": "estate-authority-registry-rotation/v1",
        "payload": rotation_payload,
    }
    rotation["prior_signature"] = base64.urlsafe_b64encode(
        attacker.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    rotation["introduced_signature"] = base64.urlsafe_b64encode(
        new_root.sign(canonical_json_bytes(signed))
    ).rstrip(b"=").decode("ascii")
    bundle["registry"]["signature"]["value"] = _signature(
        new_root, bundle["registry"]["schema_version"], registry_payload
    )
    bundle["head"]["payload"]["sequence"] = 2
    bundle["head"]["payload"]["predecessor_digest"] = previous["head_digest"]
    bundle["selections"][0]["payload"]["sequence"] = 2
    bundle["selections"][0]["payload"]["predecessor_digest"] = previous["head_digest"]
    _resign_selection(bundle, identities, 0)
    _refresh_bundle(bundle, identities)

    with pytest.raises(EstateAuthorityError, match="authority_registry_key_binding_changed"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=previous,
        )


def test_registry_transition_cannot_extend_an_existing_key_validity_window() -> None:
    bundle, identities = _build_bundle()
    first = validate_authority_bundle(
        copy.deepcopy(bundle),
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    bundle["registry"]["payload"]["keys"][0]["not_after"] = (
        "2026-09-04T00:00:00Z"
    )
    new_root = _rotate_registry(bundle, identities)
    _advance_head_for_registry(bundle, identities, first["high_water"], new_root)

    with pytest.raises(EstateAuthorityError, match="authority_registry_key_binding_changed"):
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
            previous=first["high_water"],
        )


def test_registry_rejects_duplicate_public_key_material_across_ids_and_purposes() -> None:
    bundle, identities = _build_bundle()
    bundle["registry"]["payload"]["keys"][1]["public_key_pem"] = bundle["registry"][
        "payload"
    ]["keys"][0]["public_key_pem"]
    _refresh_bundle(bundle, identities, registry_key=identities["root_key"])
    _expect_code(
        bundle,
        identities["registry_digest"],
        "authority_registry_key_material_duplicate",
    )


def test_cumulative_selection_tombstone_does_not_freeze_the_next_head() -> None:
    bundle, identities = _build_bundle(include_second=True, revoke_second=True)
    previous = _high_water(
        validate_authority_bundle(
            bundle,
            expected_registry_digest=identities["registry_digest"],
            now=NOW,
        )
    )
    prior_head = previous["head_digest"]
    bundle["selections"] = [bundle["selections"][0]]
    bundle["head"]["payload"]["sequence"] = 2
    bundle["head"]["payload"]["predecessor_digest"] = prior_head
    bundle["head"]["payload"]["revoked_selection_digests"] = []
    bundle["selections"][0]["payload"]["sequence"] = 2
    bundle["selections"][0]["payload"]["predecessor_digest"] = prior_head
    _resign_selection(bundle, identities, 0)
    _refresh_bundle(bundle, identities)

    result = validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
        previous=previous,
    )
    assert result["sequence"] == 2
    assert result["revoked_selection_digests"] == previous[
        "revoked_selection_digests"
    ]


def test_projection_is_detached_from_mutable_input() -> None:
    bundle, identities = _build_bundle()
    result = validate_authority_bundle(
        bundle,
        expected_registry_digest=identities["registry_digest"],
        now=NOW,
    )
    projected = copy.deepcopy(result["projection"])
    bundle["selections"][0]["payload"]["path"] = "attacker-controlled.md"
    bundle["selections"][0]["payload"]["supersedes"].append("selection-guidance")
    assert result["projection"] == projected


@pytest.mark.parametrize(
    "path",
    [
        ("registry", "payload", "registry_epoch"),
        ("registry", "payload", "sequence"),
        ("head", "payload", "authority_epoch"),
        ("head", "payload", "sequence"),
        ("selections", 0, "payload", "sequence"),
    ],
)
def test_contract_rejects_integers_above_javascript_safe_max(path: tuple[object, ...]) -> None:
    bundle, identities = _build_bundle()
    target = bundle
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] = 9_007_199_254_740_992
    _expect_code(bundle, identities["registry_digest"], "authority_bundle_schema_invalid")


def test_selection_must_outlive_head_strictly() -> None:
    bundle, identities = _build_bundle()
    bundle["selections"][0]["payload"]["expires_at"] = bundle["head"]["payload"][
        "expires_at"
    ]
    _resign_selection(bundle, identities, 0)
    _refresh_bundle(bundle, identities)
    _expect_code(bundle, identities["registry_digest"], "authority_selection_expired")


def _walk_json(value: object) -> list[tuple[str, object]]:
    found: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            found.append((key, child))
            found.extend(_walk_json(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_json(child))
    return found


def test_checked_fixtures_validate_and_expose_only_public_contract_fields() -> None:
    prohibited_keys = {
        "access_token",
        "api_key",
        "bearer_token",
        "client_secret",
        "credential",
        "password",
        "private_key",
        "private_key_pem",
        "refresh_token",
        "seed",
    }
    for name in ("valid-bundle.json", "revoked-bundle.json"):
        fixture_path = FIXTURE_ROOT / name
        raw = fixture_path.read_text(encoding="utf-8")
        assert "PRIVATE KEY" not in raw
        assert "BEGIN OPENSSH PRIVATE" not in raw
        fixture = json.loads(raw)
        assert not ({key.casefold() for key, _ in _walk_json(fixture)} & prohibited_keys)
        registry_digest = sha256_digest(canonical_json_bytes(fixture["registry"]))
        result = validate_authority_bundle(
            fixture,
            expected_registry_digest=registry_digest,
            now=NOW,
        )
        assert result["projection"]["schema_version"] == "estate-authority-selections/v1"


def test_governance_linkage_is_dark_and_points_to_exact_contract_evidence() -> None:
    linkage = _load_json(ROOT / "standards" / "governance" / "estate-authority-v1.json")
    assert linkage["schema_version"] == "estate-authority-governance-linkage/v1"
    assert linkage["owner"] == "standards-control-plane"
    assert linkage["consumer"] == "mapp-doc-agent"
    assert linkage["activation"] == "dark_contract"
    assert linkage["private_key_material"] == "prohibited"
    assert linkage["high_water_schema_version"] == "estate-authority-high-water/v1"
    assert linkage["retired_key_material_tombstones"] == "required"
    expected_artifacts = {
        "docs/requirements/REQ-SCP-ESTATE-AUTHORITY-001.md",
        "docs/strategy/STRAT-SCP-ESTATE-AUTHORITY-001.md",
        "docs/architecture/ARCH-SCP-ESTATE-AUTHORITY-001.md",
        "docs/plans/PLAN-SCP-ESTATE-AUTHORITY-001.md",
        "schemas/estate-authority/v1/authority-registry.schema.json",
        "schemas/estate-authority/v1/authority-bundle.schema.json",
        "schemas/estate-authority/v1/authority-high-water.schema.json",
        "src/standards_control_plane/estate_authority.py",
        "tests/test_estate_authority_contract.py",
        "fixtures/estate-authority/v1/valid-bundle.json",
        "fixtures/estate-authority/v1/revoked-bundle.json",
    }
    assert set(linkage["artifacts"]) == expected_artifacts
    assert len(linkage["artifacts"]) == len(expected_artifacts)
    for relative_path in expected_artifacts:
        assert (ROOT / relative_path).is_file()
