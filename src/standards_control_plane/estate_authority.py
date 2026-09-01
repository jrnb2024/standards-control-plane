"""Fail-closed validation for the SCP estate document-authority contract.

This module validates public, signed data only. It never creates keys, signs records,
performs network/filesystem lookups, or persists anti-rollback state.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Never, cast

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "schemas" / "estate-authority" / "v1"
DIGEST_PREFIX = "sha256:"
MAX_HEAD_LIFETIME = timedelta(hours=24)
MAX_CLOCK_SKEW = timedelta(seconds=5)
MAX_PROJECTED_BYTES = 4 * 1024 * 1024
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}$")


class EstateAuthorityError(ValueError):
    """Stable fail-closed authority validation error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> Never:
    raise EstateAuthorityError(code)


def canonical_json_bytes(value: object) -> bytes:
    """Return the contract's deterministic compact UTF-8 JSON representation."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError):
        _fail("authority_canonicalization_invalid")


def sha256_digest(value: bytes) -> str:
    return f"{DIGEST_PREFIX}{hashlib.sha256(value).hexdigest()}"


def _is_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith(DIGEST_PREFIX)
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _load_schema(name: str) -> dict[str, Any]:
    loaded = json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))
    return cast(dict[str, Any], loaded)


def _validate_schema(bundle: object) -> None:
    registry_schema = _load_schema("authority-registry.schema.json")
    bundle_schema = _load_schema("authority-bundle.schema.json")
    registry = Registry().with_resource(
        registry_schema["$id"], Resource.from_contents(registry_schema)
    )
    validator = Draft202012Validator(
        bundle_schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(bundle), key=lambda error: list(error.absolute_path))
    if errors:
        _fail("authority_bundle_schema_invalid")


def _timestamp(value: str, code: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        _fail(code)
    if parsed.tzinfo is None:
        _fail(code)
    return parsed.astimezone(UTC)


def _public_key(pem: str, code: str) -> Ed25519PublicKey:
    try:
        key = serialization.load_pem_public_key(pem.encode("ascii"))
    except (TypeError, ValueError):
        _fail(code)
    if not isinstance(key, Ed25519PublicKey):
        _fail(code)
    return key


def _signature_bytes(value: str, code: str) -> bytes:
    try:
        decoded = base64.urlsafe_b64decode(value + "==")
    except (ValueError, TypeError):
        _fail(code)
    if len(decoded) != 64:
        _fail(code)
    return decoded


def _verify_signature(
    public_key: Ed25519PublicKey,
    signature_value: str,
    signed_value: object,
    code: str,
) -> None:
    try:
        public_key.verify(
            _signature_bytes(signature_value, code),
            canonical_json_bytes(signed_value),
        )
    except InvalidSignature:
        _fail(code)


def _signed_value(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": envelope["schema_version"],
        "payload": envelope["payload"],
    }


def _registry_rotation_signed_value(payload: Mapping[str, Any]) -> dict[str, Any]:
    rotation = payload["rotation"]
    rotation_core = {
        key: value
        for key, value in rotation.items()
        if key not in {"prior_signature", "introduced_signature"}
    }
    registry_core = dict(payload)
    registry_core["rotation"] = rotation_core
    return {
        "schema_version": "estate-authority-registry-rotation/v1",
        "payload": registry_core,
    }


def _key_valid_at(key: Mapping[str, Any], at: datetime) -> bool:
    not_before = _timestamp(key["not_before"], "authority_registry_time_invalid")
    not_after = _timestamp(key["not_after"], "authority_registry_time_invalid")
    return not_before <= at < not_after and not_after > not_before


def _validate_key_window(key: Mapping[str, Any]) -> None:
    not_before = _timestamp(key["not_before"], "authority_registry_time_invalid")
    not_after = _timestamp(key["not_after"], "authority_registry_time_invalid")
    if not_after <= not_before:
        _fail("authority_registry_key_invalid")


def _validate_registry(
    envelope: Mapping[str, Any],
    *,
    expected_registry_digest: str,
    now: datetime,
) -> tuple[str, dict[str, Mapping[str, Any]], dict[str, Ed25519PublicKey]]:
    registry_digest = sha256_digest(canonical_json_bytes(envelope))
    if registry_digest != expected_registry_digest:
        _fail("authority_registry_digest_mismatch")

    payload = envelope["payload"]
    issued_at = _timestamp(payload["issued_at"], "authority_registry_time_invalid")
    expires_at = _timestamp(payload["expires_at"], "authority_registry_time_invalid")
    if issued_at > now + MAX_CLOCK_SKEW or expires_at <= now or expires_at <= issued_at:
        _fail("authority_registry_expired")

    keys: dict[str, Mapping[str, Any]] = {}
    public_keys: dict[str, Ed25519PublicKey] = {}
    for key in payload["keys"]:
        key_id = key["key_id"]
        if key_id in keys:
            _fail("authority_registry_key_duplicate")
        public_key = _public_key(key["public_key_pem"], "authority_registry_key_invalid")
        _validate_key_window(key)
        keys[key_id] = key
        public_keys[key_id] = public_key

    signature = envelope["signature"]
    signer = keys.get(signature["key_id"])
    if (
        signer is None
        or signer["purpose"] != "estate-authority-registry-root"
        or signer["status"] != "active"
        or not _key_valid_at(signer, now)
        or not _key_valid_at(signer, issued_at)
    ):
        _fail("authority_registry_signer_rejected")
    _verify_signature(
        public_keys[signature["key_id"]],
        signature["value"],
        _signed_value(envelope),
        "authority_registry_signature_invalid",
    )

    rotation = payload["rotation"]
    if payload["sequence"] == 1:
        if payload["predecessor_digest"] is not None or rotation is not None:
            _fail("authority_registry_sequence_invalid")
    else:
        if payload["predecessor_digest"] is None or rotation is None:
            _fail("authority_registry_rotation_required")
        if rotation["prior_registry_digest"] != payload["predecessor_digest"]:
            _fail("authority_registry_rotation_invalid")
        prior = keys.get(rotation["prior_key_id"])
        introduced = keys.get(rotation["introduced_key_id"])
        if (
            prior is None
            or introduced is None
            or prior["purpose"] != "estate-authority-registry-root"
            or prior["status"] not in {"active", "revoked"}
            or introduced["purpose"] != "estate-authority-registry-root"
            or introduced["status"] not in {"active", "next"}
            or rotation["prior_key_id"] == rotation["introduced_key_id"]
            or not _key_valid_at(prior, issued_at)
            or not _key_valid_at(introduced, issued_at)
        ):
            _fail("authority_registry_rotation_invalid")
        signed = _registry_rotation_signed_value(payload)
        _verify_signature(
            public_keys[rotation["prior_key_id"]],
            rotation["prior_signature"],
            signed,
            "authority_registry_rotation_signature_invalid",
        )
        _verify_signature(
            public_keys[rotation["introduced_key_id"]],
            rotation["introduced_signature"],
            signed,
            "authority_registry_rotation_signature_invalid",
        )
    return registry_digest, keys, public_keys


def _validate_head_times(payload: Mapping[str, Any], now: datetime) -> tuple[datetime, datetime]:
    issued_at = _timestamp(payload["issued_at"], "authority_head_time_invalid")
    expires_at = _timestamp(payload["expires_at"], "authority_head_time_invalid")
    if issued_at > now + MAX_CLOCK_SKEW:
        _fail("authority_head_time_invalid")
    if expires_at <= now:
        _fail("authority_head_expired")
    if expires_at <= issued_at or expires_at - issued_at > MAX_HEAD_LIFETIME:
        _fail("authority_head_time_invalid")
    return issued_at, expires_at


def _validate_sorted_unique(values: list[str], code: str) -> None:
    if values != sorted(values) or len(values) != len(set(values)):
        _fail(code)


def _head_core(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in {"head_digest", "selection_digest"}
    }


def _selection_sort_key(envelope: Mapping[str, Any]) -> tuple[str, str, str]:
    payload = envelope["payload"]
    return (payload["repository_id"], payload["path"], payload["selection_id"])


def _validate_epoch_transition(
    payload: Mapping[str, Any],
    previous: Mapping[str, Any],
    keys: Mapping[str, Mapping[str, Any]],
    public_keys: Mapping[str, Ed25519PublicKey],
) -> None:
    transition = payload["epoch_transition"]
    if transition is None:
        _fail("authority_epoch_transition_required")
    expected = {
        "previous_authority_epoch": previous["authority_epoch"],
        "previous_head_digest": previous["head_digest"],
        "previous_registry_digest": previous["registry_digest"],
        "new_authority_epoch": payload["authority_epoch"],
    }
    if any(transition[field] != value for field, value in expected.items()):
        _fail("authority_epoch_transition_invalid")
    prior_key = keys.get(transition["previous_root_key_id"])
    new_key = keys.get(transition["new_root_key_id"])
    if (
        prior_key is None
        or new_key is None
        or prior_key["purpose"] != "estate-authority-registry-root"
        or prior_key["status"] not in {"active", "revoked"}
        or new_key["purpose"] != "estate-authority-registry-root"
        or new_key["status"] != "active"
        or transition["previous_root_key_id"] == transition["new_root_key_id"]
    ):
        _fail("authority_epoch_transition_invalid")
    transition_payload = {
        key: value
        for key, value in transition.items()
        if key not in {"previous_signature", "new_signature"}
    }
    signed = {
        "schema_version": "estate-authority-epoch-transition/v1",
        "payload": transition_payload,
    }
    _verify_signature(
        public_keys[transition["previous_root_key_id"]],
        transition["previous_signature"],
        signed,
        "authority_epoch_transition_signature_invalid",
    )
    _verify_signature(
        public_keys[transition["new_root_key_id"]],
        transition["new_signature"],
        signed,
        "authority_epoch_transition_signature_invalid",
    )


def _validate_previous_state(previous: Mapping[str, Any] | None) -> None:
    if previous is None:
        return
    required = {
        "authority_epoch",
        "sequence",
        "head_digest",
        "registry_epoch",
        "registry_sequence",
        "registry_digest",
        "registry_revoked_key_ids",
        "revoked_selection_digests",
    }
    if (
        set(previous) != required
        or not isinstance(previous["authority_epoch"], int)
        or isinstance(previous["authority_epoch"], bool)
        or previous["authority_epoch"] < 1
        or not isinstance(previous["sequence"], int)
        or isinstance(previous["sequence"], bool)
        or previous["sequence"] < 1
        or not isinstance(previous["registry_epoch"], int)
        or isinstance(previous["registry_epoch"], bool)
        or previous["registry_epoch"] < 1
        or not isinstance(previous["registry_sequence"], int)
        or isinstance(previous["registry_sequence"], bool)
        or previous["registry_sequence"] < 1
        or not _is_digest(previous["head_digest"])
        or not _is_digest(previous["registry_digest"])
        or not isinstance(previous["registry_revoked_key_ids"], list)
        or any(
            not isinstance(key_id, str) or ID_PATTERN.fullmatch(key_id) is None
            for key_id in previous["registry_revoked_key_ids"]
        )
        or previous["registry_revoked_key_ids"]
        != sorted(set(previous["registry_revoked_key_ids"]))
        or not isinstance(previous["revoked_selection_digests"], list)
        or any(not _is_digest(value) for value in previous["revoked_selection_digests"])
        or previous["revoked_selection_digests"]
        != sorted(set(previous["revoked_selection_digests"]))
    ):
        _fail("authority_previous_state_invalid")


def _validate_registry_anti_rollback(
    payload: Mapping[str, Any],
    registry_digest: str,
    previous: Mapping[str, Any] | None,
) -> None:
    if previous is None:
        return
    current_keys = {key["key_id"]: key for key in payload["keys"]}
    for key_id in previous["registry_revoked_key_ids"]:
        if key_id not in current_keys or current_keys[key_id]["status"] != "revoked":
            _fail("authority_registry_key_resurrection")
    if registry_digest == previous["registry_digest"]:
        if (
            payload["registry_epoch"] != previous["registry_epoch"]
            or payload["sequence"] != previous["registry_sequence"]
        ):
            _fail("authority_registry_fork")
        return
    if payload["registry_epoch"] < previous["registry_epoch"]:
        _fail("authority_registry_rollback")
    if (
        payload["registry_epoch"] == previous["registry_epoch"]
        and payload["sequence"] <= previous["registry_sequence"]
    ):
        _fail("authority_registry_rollback")
    rotation = payload["rotation"]
    if rotation is None or rotation["prior_registry_digest"] != previous["registry_digest"]:
        _fail("authority_registry_predecessor_mismatch")


def _validate_anti_rollback(
    payload: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
    keys: Mapping[str, Mapping[str, Any]],
    public_keys: Mapping[str, Ed25519PublicKey],
) -> None:
    if previous is None:
        if payload["epoch_transition"] is not None:
            _fail("authority_epoch_transition_unexpected")
        return
    epoch = payload["authority_epoch"]
    sequence = payload["sequence"]
    if epoch < previous["authority_epoch"]:
        _fail("authority_head_rollback")
    if epoch == previous["authority_epoch"]:
        if payload["epoch_transition"] is not None:
            _fail("authority_epoch_transition_unexpected")
        if sequence < previous["sequence"]:
            _fail("authority_head_rollback")
        if sequence == previous["sequence"]:
            if payload["head_digest"] != previous["head_digest"]:
                _fail("authority_head_fork")
            return
        if payload["predecessor_digest"] != previous["head_digest"]:
            _fail("authority_head_predecessor_mismatch")
        return
    _validate_epoch_transition(payload, previous, keys, public_keys)


def _validate_supersession(rows: list[Mapping[str, Any]]) -> None:
    by_id = {row["selection_id"]: row for row in rows}
    for row in rows:
        for target in row["supersedes"]:
            if target not in by_id or by_id[target]["lifecycle"] != "superseded":
                _fail("authority_supersession_invalid")

    state: dict[str, int] = {}
    for root_id in sorted(by_id):
        if state.get(root_id) == 2:
            continue
        stack: list[tuple[str, int]] = [(root_id, 0)]
        while stack:
            selection_id, next_index = stack[-1]
            state.setdefault(selection_id, 1)
            targets = by_id[selection_id]["supersedes"]
            if next_index >= len(targets):
                state[selection_id] = 2
                stack.pop()
                continue
            target = targets[next_index]
            stack[-1] = (selection_id, next_index + 1)
            if state.get(target) == 1:
                _fail("authority_supersession_cycle")
            if state.get(target) != 2:
                stack.append((target, 0))


def validate_authority_bundle(
    bundle: object,
    *,
    expected_registry_digest: str,
    now: datetime | None = None,
    previous: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate an authority bundle and return the exact doc-agent projection."""

    _validate_schema(bundle)
    if not _is_digest(expected_registry_digest):
        _fail("authority_registry_digest_invalid")
    if now is not None and now.tzinfo is None:
        _fail("authority_validation_time_invalid")
    at = now.astimezone(UTC) if now is not None else datetime.now(UTC)
    if not isinstance(bundle, Mapping):
        _fail("authority_bundle_schema_invalid")
    typed_bundle = cast(Mapping[str, Any], bundle)
    _validate_previous_state(previous)

    registry_digest, keys, public_keys = _validate_registry(
        typed_bundle["registry"],
        expected_registry_digest=expected_registry_digest,
        now=at,
    )
    registry_payload = typed_bundle["registry"]["payload"]
    _validate_registry_anti_rollback(registry_payload, registry_digest, previous)
    head = cast(Mapping[str, Any], typed_bundle["head"])
    head_payload = head["payload"]
    issued_at, head_expiry = _validate_head_times(head_payload, at)
    registry_issued_at = _timestamp(
        registry_payload["issued_at"], "authority_registry_time_invalid"
    )
    registry_expiry = _timestamp(
        registry_payload["expires_at"], "authority_registry_time_invalid"
    )
    if issued_at < registry_issued_at or head_expiry > registry_expiry:
        _fail("authority_head_registry_window_invalid")
    if head_payload["selector_registry_digest"] != registry_digest:
        _fail("authority_head_registry_digest_mismatch")

    _validate_sorted_unique(head_payload["active_key_ids"], "authority_head_key_set_invalid")
    _validate_sorted_unique(head_payload["revoked_key_ids"], "authority_head_key_set_invalid")
    _validate_sorted_unique(
        head_payload["revoked_selection_digests"], "authority_revocation_set_invalid"
    )
    active_key_ids = set(head_payload["active_key_ids"])
    revoked_key_ids = set(head_payload["revoked_key_ids"])
    if active_key_ids & revoked_key_ids:
        _fail("authority_head_key_set_invalid")
    for key_id in active_key_ids:
        key = keys.get(key_id)
        if (
            key is None
            or key["purpose"] != "estate-document-authority-selection"
            or key["status"] != "active"
            or not _key_valid_at(key, at)
            or not _key_valid_at(key, issued_at)
        ):
            _fail("authority_head_key_rejected")
    for key_id in revoked_key_ids:
        key = keys.get(key_id)
        if key is None or key["status"] != "revoked":
            _fail("authority_head_key_set_invalid")

    head_signer_id = head["signature"]["key_id"]
    if head_signer_id not in active_key_ids:
        _fail("authority_head_signer_rejected")

    expected_head_digest = sha256_digest(canonical_json_bytes(_head_core(head_payload)))
    if expected_head_digest != head_payload["head_digest"]:
        _fail("authority_head_digest_mismatch")
    _verify_signature(
        public_keys[head_signer_id],
        head["signature"]["value"],
        _signed_value(head),
        "authority_head_signature_invalid",
    )

    selection_envelopes = sorted(
        cast(list[Mapping[str, Any]], typed_bundle["selections"]),
        key=_selection_sort_key,
    )
    revoked_selection_digests = set(head_payload["revoked_selection_digests"])
    if previous is not None and any(
        value not in revoked_selection_digests
        for value in previous["revoked_selection_digests"]
    ):
        _fail("authority_selection_revocation_tombstone_removed")
    envelope_digests = {
        sha256_digest(canonical_json_bytes(envelope)) for envelope in selection_envelopes
    }
    if not revoked_selection_digests <= envelope_digests:
        _fail("authority_revocation_target_missing")
    expected_revocation_digest = sha256_digest(
        canonical_json_bytes(
            {
                "revoked_key_ids": head_payload["revoked_key_ids"],
                "revoked_selection_digests": head_payload["revoked_selection_digests"],
            }
        )
    )
    if expected_revocation_digest != head_payload["revocation_digest"]:
        _fail("authority_revocation_digest_mismatch")

    rows: list[Mapping[str, Any]] = []
    seen_ids: set[str] = set()
    seen_bindings: set[tuple[str, str]] = set()
    lifecycle_pairs = {
        "canonical": "canonical",
        "active": "active_noncanonical",
        "superseded": "superseded",
    }
    for envelope in selection_envelopes:
        row = envelope["payload"]
        selection_id = row["selection_id"]
        binding = (row["repository_id"], row["path"])
        if selection_id in seen_ids or binding in seen_bindings:
            _fail("authority_selection_duplicate")
        seen_ids.add(selection_id)
        seen_bindings.add(binding)
        signer_id = envelope["signature"]["key_id"]
        if signer_id != row["selector_id"] or signer_id not in active_key_ids:
            _fail("authority_selection_signer_rejected")
        if len(row["path"].encode("utf-8")) > 512:
            _fail("authority_selection_path_invalid")
        if lifecycle_pairs[row["lifecycle"]] != row["authority"]:
            _fail("authority_selection_lifecycle_invalid")
        if row["sequence"] != head_payload["sequence"]:
            _fail("authority_selection_sequence_mismatch")
        if row["predecessor_digest"] != head_payload["predecessor_digest"]:
            _fail("authority_selection_predecessor_mismatch")
        selection_expiry = _timestamp(row["expires_at"], "authority_selection_time_invalid")
        if selection_expiry <= at or selection_expiry < head_expiry:
            _fail("authority_selection_expired")
        _verify_signature(
            public_keys[signer_id],
            envelope["signature"]["value"],
            _signed_value(envelope),
            "authority_selection_signature_invalid",
        )
        envelope_digest = sha256_digest(canonical_json_bytes(envelope))
        if envelope_digest not in revoked_selection_digests:
            rows.append(row)

    expected_envelopes_digest = sha256_digest(
        canonical_json_bytes({"selections": selection_envelopes})
    )
    if expected_envelopes_digest != head_payload["selection_envelopes_digest"]:
        _fail("authority_selection_envelopes_digest_mismatch")

    _validate_supersession(rows)
    projection = {
        "schema_version": "estate-authority-selections/v1",
        "authority_epoch": head_payload["authority_epoch"],
        "sequence": head_payload["sequence"],
        "head_digest": head_payload["head_digest"],
        "selections": rows,
    }
    projection_bytes = canonical_json_bytes(projection)
    if len(projection_bytes) > MAX_PROJECTED_BYTES:
        _fail("authority_projection_too_large")
    selection_digest = sha256_digest(projection_bytes)
    if selection_digest != head_payload["selection_digest"]:
        _fail("authority_selection_digest_mismatch")

    _validate_anti_rollback(head_payload, previous, keys, public_keys)
    return {
        "schema_version": "estate-authority-validation/v1",
        "authority_epoch": head_payload["authority_epoch"],
        "sequence": head_payload["sequence"],
        "head_digest": head_payload["head_digest"],
        "registry_epoch": registry_payload["registry_epoch"],
        "registry_sequence": registry_payload["sequence"],
        "registry_revoked_key_ids": sorted(
            key["key_id"] for key in registry_payload["keys"] if key["status"] == "revoked"
        ),
        "revoked_selection_digests": sorted(revoked_selection_digests),
        "selection_envelopes_digest": expected_envelopes_digest,
        "selection_digest": selection_digest,
        "revocation_digest": head_payload["revocation_digest"],
        "registry_digest": registry_digest,
        "issued_at": head_payload["issued_at"],
        "expires_at": head_payload["expires_at"],
        "projection": projection,
    }
