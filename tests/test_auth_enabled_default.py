"""AUTH_ENABLED must fail closed when the environment does not set it.

The default was False, so a deployment that shipped without `AUTH_ENABLED` in
its environment served the API unauthenticated. The shipped env files all set
it (`.env:3`, `.env.example:3`, `.env.staging.example:3`) and the Estate
read-only profile guards it, so real deployments were covered — but the safety
came from the environment, not from the code.

These tests pin the default itself, and drive the real app rather than only
asserting on the config object, because a config assertion cannot observe
whether a request is actually refused.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_service_api import _write_overlay

from standards_control_plane.service import ServiceConfig, create_app

# A deployment whose environment simply forgot AUTH_ENABLED. Everything else
# needed for a non-development boot is present.
_ENV_WITHOUT_AUTH_ENABLED = {
    "ENV": "staging",
    "PUBLIC_BASE_URL": "https://scp.brokapps.ai",
    "CT_APP_ID": "scp",
}


def test_auth_enabled_defaults_to_true_when_unset() -> None:
    config = ServiceConfig.from_env(env=_ENV_WITHOUT_AUTH_ENABLED)
    assert config.auth_enabled is True


def test_auth_enabled_defaults_to_true_on_an_unrecognised_value() -> None:
    """A typo must not silently open the service."""
    config = ServiceConfig.from_env(env={**_ENV_WITHOUT_AUTH_ENABLED, "AUTH_ENABLED": "maybe"})
    assert config.auth_enabled is True


@pytest.mark.parametrize("value", ["false", "0", "no", "off"])
def test_auth_can_still_be_turned_off_explicitly(value: str) -> None:
    """The opt-out must keep working, or the default above proves nothing."""
    config = ServiceConfig.from_env(env={**_ENV_WITHOUT_AUTH_ENABLED, "AUTH_ENABLED": value})
    assert config.auth_enabled is False


def test_auth_mode_is_oidc_not_none_when_unset() -> None:
    config = ServiceConfig.from_env(env=_ENV_WITHOUT_AUTH_ENABLED)
    assert config.auth_mode() == "oidc"


# ── The kill: an unauthenticated API request must actually be refused ──


def test_api_request_is_refused_when_auth_enabled_is_unset(tmp_path: Path) -> None:
    overlay_root = _write_overlay(tmp_path / "overlay")
    app = create_app(
        overlay_paths=[str(overlay_root)],
        env={
            "ENV": "development",
            "PUBLIC_BASE_URL": "http://testserver",
            "CT_APP_ID": "scp-dev",
        },
    )

    with TestClient(app) as client:
        response = client.get("/registry")

    assert response.status_code == 401, (
        "unauthenticated API request was served with AUTH_ENABLED unset; "
        f"status={response.status_code}"
    )


def test_api_request_is_served_when_auth_explicitly_disabled(tmp_path: Path) -> None:
    """Proves the 401 above is a real gate, not one that cannot pass."""
    overlay_root = _write_overlay(tmp_path / "overlay")
    app = create_app(
        overlay_paths=[str(overlay_root)],
        env={"AUTH_ENABLED": "false", "ENV": "development"},
    )

    with TestClient(app) as client:
        response = client.get("/registry")

    assert response.status_code == 200
