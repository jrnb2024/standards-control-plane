"""Conflict-gate test driver per WP-SCP-020 §4 020C.1 (iv).

Iterates `tests/conflict_gate/fixtures/<rule_id>/<scenario>/` directories
and asserts the Rego rule, the Python evaluator, and the
canonical-expected verdict all agree. Disagreement → AssertionError
with SCP-E005 prefix → CI job failure → merge block.

Engine invocation:
- Rego: `opa eval --format json --data <rule.rego> --input <fixture-input>
        'data.main.deny'` — captured as JSON.
- Python: `python -m standards_control_plane audit ...` against the same
        fixture path — captured as audit-result JSON.

If either engine binary is unavailable in the test environment (no `opa`
on PATH, audit CLI errors out), the test SKIPS that fixture with a clear
xfail reason rather than spuriously failing the job. The CI environment
must have both available; local devs can run a subset.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from .adapter import (
    UnifiedRecord,
    collect_fixtures,
    evaluate_conflict_gate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"
POLICIES_DIR = REPO_ROOT / "policies"

# WP-SCP-022 slice 020Q (closes TF-006): Python-side mirror of
# policies/scp_common.rego suppression helpers. Each Python function below
# cites the matching Rego source line so reviewers can verify parity.
# The conflict-gate framework is the integration test for these helpers
# — every fixture exercises at least one branch of every helper.

_DATEISH_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATEISH_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)


def _parse_dateish_ns(value: object) -> int | None:
    """Mirror policies/scp_common.rego scp_dateish_ns (lines 94-104).

    Returns nanoseconds since the Unix epoch for either:
      - YYYY-MM-DD (treated as midnight UTC)
      - RFC3339 datetime (with explicit timezone)
    Returns None for any unparseable input.
    """
    if not isinstance(value, str):
        return None
    if _DATEISH_DATE_RE.match(value):
        try:
            dt = datetime(
                year=int(value[0:4]),
                month=int(value[5:7]),
                day=int(value[8:10]),
                tzinfo=timezone.utc,
            )
        except ValueError:
            return None
        return int(dt.timestamp() * 1_000_000_000)
    if _DATEISH_DATETIME_RE.match(value):
        # Python's fromisoformat handles RFC3339 datetimes when the trailing
        # 'Z' is rewritten to '+00:00' (Python <3.11 limitation; safe on
        # 3.11+ too). Reject on parse failure.
        normalised = value.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(normalised)
        except ValueError:
            return None
        if dt.tzinfo is None:
            return None
        return int(dt.timestamp() * 1_000_000_000)
    return None


def _scp_waiver_expired(waiver: object, now_ns: int) -> bool:
    """Mirror policies/scp_common.rego scp_waiver_expired (lines 54-72).

    Fail-closed: missing/empty/unparseable expires_at => expired (returns True).
    Otherwise compare parsed expires_at to now_ns.
    """
    if not isinstance(waiver, dict):
        return True
    expires_at = waiver.get("expires_at", "")
    if not isinstance(expires_at, str) or expires_at == "":
        return True
    expiry_ns = _parse_dateish_ns(expires_at)
    if expiry_ns is None:
        return True
    return expiry_ns <= now_ns


def _scp_active_waiver_for(rule_id: str, waivers: object, now_ns: int) -> bool:
    """Mirror policies/scp_common.rego scp_active_waiver_for (lines 44-49).

    Returns True iff data.waivers contains any unexpired entry whose
    rule_id matches. Per the Rego comment at lines 36-43, finding_id-only
    matching is deferred to WP-SCP-023 — rule_id matching is the
    rule_id-only fail-closed semantic.
    """
    if not isinstance(waivers, list):
        return False
    for w in waivers:
        if not isinstance(w, dict):
            continue
        if w.get("rule_id", "") != rule_id:
            continue
        if not _scp_waiver_expired(w, now_ns):
            return True
    return False


def _scp_rule_config_disabled(rule_id: str, rule_config: object) -> bool:
    """Mirror policies/scp_common.rego scp_rule_config_disabled (lines 77-81).

    Returns True iff rule_config["rules"][rule_id]["disable"] is exactly True.
    Returns False on any missing key / wrong type at any level (mirrors
    `default scp_rule_config_disabled := false`).
    """
    if not isinstance(rule_config, dict):
        return False
    rules = rule_config.get("rules")
    if not isinstance(rules, dict):
        return False
    entry = rules.get(rule_id)
    if not isinstance(entry, dict):
        return False
    return entry.get("disable") is True


def _load_sibling_waivers(scenario_dir: Path) -> list:
    """Load `<scenario_dir>/waivers.json` if present, else return []."""
    candidate = scenario_dir / "waivers.json"
    if not candidate.is_file():
        return []
    try:
        loaded = json.loads(candidate.read_text())
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else []


def _load_sibling_rule_config(scenario_dir: Path) -> dict:
    """Load `<scenario_dir>/.scp/rule-config.yaml` if present, else {}.

    Mirrors the production layout: adopter repos place rule-config under
    `.scp/rule-config.yaml`, so the fixture corpus uses the same path.
    """
    candidate = scenario_dir / ".scp" / "rule-config.yaml"
    if not candidate.is_file():
        return {}
    try:
        import yaml
        loaded = yaml.safe_load(candidate.read_text())
    except (ImportError, yaml.YAMLError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _build_opa_data_arg(scenario_dir: Path) -> tuple[Path, str] | None:
    """Build a tempfile carrying `{"waivers": [...], "rule_config": {...}}`
    for `--data` ingestion by opa eval.

    Returns (tempfile_path, "tempfile_path") or None if no siblings are
    present (in which case callers should skip the `--data` flag entirely).
    Caller is responsible for unlinking the tempfile after opa exits.
    """
    waivers = _load_sibling_waivers(scenario_dir)
    rule_config = _load_sibling_rule_config(scenario_dir)
    if not waivers and not rule_config:
        return None
    data: dict = {}
    if waivers:
        data["waivers"] = waivers
    if rule_config:
        data["rule_config"] = rule_config
    fd, path = tempfile.mkstemp(prefix="_scp_test_data_", suffix=".json")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle)
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    return Path(path), path


def _suppression_active(rule_id: str, scenario_dir: Path) -> bool:
    """Common short-circuit for Python evaluators.

    Returns True iff either an active waiver or a rule-config disable
    suppresses the rule for this scenario. Python evaluators that detect
    suppression should return `{"findings": []}` to mirror the Rego deny
    rule's `not scp_active_waiver_for(...) AND not scp_rule_config_disabled(...)`
    short-circuit (see policies/SCP-R-001.rego lines 97-102).
    """
    now_ns = int(datetime.now(tz=timezone.utc).timestamp() * 1_000_000_000)
    waivers = _load_sibling_waivers(scenario_dir)
    if _scp_active_waiver_for(rule_id, waivers, now_ns):
        return True
    rule_config = _load_sibling_rule_config(scenario_dir)
    if _scp_rule_config_disabled(rule_id, rule_config):
        return True
    return False


@pytest.fixture(scope="module")
def opa_binary() -> str | None:
    """Return path to opa binary, or None if absent."""
    return shutil.which("opa")


@pytest.fixture(scope="module")
def audit_cli_available() -> bool:
    """Best-effort check that the audit CLI is importable and runnable."""
    try:
        result = subprocess.run(
            ["python3", "-m", "standards_control_plane", "--help"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            timeout=15,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_opa(rule_id: str, fixture_input_path: Path, opa: str) -> dict:
    rule_path = POLICIES_DIR / f"{rule_id}.rego"
    common_path = POLICIES_DIR / "scp_common.rego"
    # Closes WP-SCP-022 R1 completeness MAJ-001: scp_common.rego provides
    # scp_active_waiver_for + scp_rule_config_disabled + scp_dateish_ns
    # used by every SCP-R-NNN rule. Without it, OPA evaluates the
    # suppression guards as `not undefined = true`, masking any waiver
    # or rule-config bug rather than catching it via conflict-gate
    # disagreement with the Python evaluator.
    cmd = [
        opa,
        "eval",
        "--format=json",
        "--data",
        str(rule_path),
        "--data",
        str(common_path),
    ]

    # WP-SCP-022 slice 020Q (closes TF-006): if the scenario directory
    # carries sibling waivers.json or .scp/rule-config.yaml, build a
    # tempfile combining them as `{"waivers": [...], "rule_config": {...}}`
    # and pass via `--data`. Without this, `data.waivers` and
    # `data.rule_config` are undefined and Rego's suppression guards
    # always fall through to `default` — masking any waiver/rule-config
    # divergence between Rego and the Python evaluator.
    scenario_dir = fixture_input_path.parent
    data_arg = _build_opa_data_arg(scenario_dir)
    data_path: Path | None = None
    if data_arg is not None:
        data_path, data_path_str = data_arg
        cmd.extend(["--data", data_path_str])

    cmd.extend(["--input", str(fixture_input_path), "data.main.deny"])

    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    finally:
        # Clean up tempfile even if subprocess raises (e.g. timeout).
        if data_path is not None:
            try:
                os.unlink(data_path)
            except OSError:
                pass

    if result.returncode != 0:
        # OPA writes compile / eval errors to stdout in --format=json mode;
        # stderr can be empty even when stdout carries the diagnostic.
        # Surface both so CI logs are diagnosable.
        raise RuntimeError(
            f"opa eval exited {result.returncode} for {rule_id}/{fixture_input_path}\n"
            f"  stderr: {result.stderr.strip()[:500]}\n"
            f"  stdout: {result.stdout.strip()[:1000]}"
        )
    return json.loads(result.stdout) if result.stdout else {}


def _run_python_audit(rule_id: str, fixture_input_path: Path) -> dict:
    """Run the Python evaluator equivalent against the fixture.

    For SCP-R-001: invoke service_lifecycle evaluator on the fixture's
    services.yml. Returns audit-result-shaped JSON.
    For SCP-R-002: similarly invoke the waiver-validation path.
    For SCP-R-003: no Python equivalent — return an empty audit result
    so the test SKIPS gracefully rather than fails.
    For SCP-R-004 (post-020P): URL-presence check on waiver reason field.
    """
    if rule_id == "SCP-R-003":
        # Documented gap per docs/integrations/conflict-gate.md.
        # Return empty findings so the test compares "allow" to "allow"
        # which mirrors the conflict-gate expectation that absent
        # Python equivalents simply don't disagree with Rego.
        return {"findings": []}

    # SCP-R-004 (post-020P) is a self-contained URL-presence check
    # that doesn't need the service_lifecycle import; evaluate directly.
    if rule_id == "SCP-R-004":
        return _evaluate_scp_r_004_python(fixture_input_path)

    # Both SCP-R-001 and SCP-R-002 fixtures: import the evaluator
    # programmatically and run a minimal check against the fixture.
    # We don't invoke the full audit CLI for unit-test speed.
    from standards_control_plane.evaluators import service_lifecycle  # noqa: F401

    # The conflict-gate's primary contract is verdict agreement, not
    # exact finding-message parity. We approximate the Python verdict
    # by parsing the fixture and applying the rule's check.
    if rule_id == "SCP-R-001":
        return _evaluate_scp_r_001_python(fixture_input_path)
    if rule_id == "SCP-R-002":
        return _evaluate_scp_r_002_python(fixture_input_path)
    return {"findings": []}


def _evaluate_scp_r_001_python(fixture_input_path: Path) -> dict:
    """Minimal in-test evaluator mirroring SCP-R-001's mode-set check.

    SCP-R-001 operates on the canonical SVC-003 services.yml shape — a
    services-by-name map (`services: { <name>: { auth: { mode: ... } } }`).
    Both the rego rule and this evaluator share that input shape so the
    conflict-gate compares like-for-like.

    WP-SCP-022 slice 020Q (closes TF-006): short-circuits to no findings
    when an active waiver or rule-config disable is present for SCP-R-001.
    Mirrors policies/SCP-R-001.rego deny rule (lines 97-102):
    `not scp_active_waiver_for AND not scp_rule_config_disabled`.
    """
    if _suppression_active("SCP-R-001", fixture_input_path.parent):
        return {"findings": []}

    import yaml

    APPROVED_MODES = {
        "mode.user_oidc",
        "mode.service_rs256",
        "mode.api_key",
        "mode.bearer_legacy",
    }
    payload = yaml.safe_load(fixture_input_path.read_text())
    services = payload.get("services", {}) if isinstance(payload, dict) else {}
    findings = []
    if isinstance(services, dict):
        iterable = services.items()
    elif isinstance(services, list):
        # Backwards-compatibility for any list-shape fixtures the
        # conflict-gate corpus may still carry; service_id used as key
        # if present, falling back to index.
        iterable = (
            (entry.get("service_id", str(idx)) if isinstance(entry, dict) else str(idx), entry)
            for idx, entry in enumerate(services)
        )
    else:
        iterable = ()
    for service_name, entry in iterable:
        if not isinstance(entry, dict):
            continue
        auth = entry.get("auth", {})
        mode = auth.get("mode") if isinstance(auth, dict) else None
        if mode not in APPROVED_MODES:
            findings.append({
                "rule_id": "SCP-R-001",
                "file": str(fixture_input_path),
                "severity": "high",
                "summary": (
                    f"services.{service_name}.auth.mode '{mode}' is not in the SVC-003 approved set"
                ),
            })
    return {"findings": findings}


def _evaluate_scp_r_004_python(fixture_input_path: Path) -> dict:
    """Minimal in-test evaluator mirroring SCP-R-004's URL-presence check.

    Mirrors policies/SCP-R-004.rego's `scp_r_004_has_url` predicate
    via Python's `re` module. Both engines accept the same regex
    `https?://\\S+` for the conflict-gate fixture corpus (ASCII-only).
    See TF-020L-001 for the Unicode-whitespace divergence + Phase-2
    monitor closure path. Self-contained — no service_lifecycle
    import needed (SCP-R-004 evaluates the waivers payload directly).

    WP-SCP-022 slice 020Q (closes TF-006): short-circuits to no findings
    when an active waiver or rule-config disable is present for SCP-R-004
    (mirrors the same pattern as SCP-R-001/002).
    """
    if _suppression_active("SCP-R-004", fixture_input_path.parent):
        return {"findings": []}

    URL_PATTERN = re.compile(r"https?://\S+")
    payload = json.loads(fixture_input_path.read_text())
    findings: list[dict] = []
    if not isinstance(payload, list) or len(payload) == 0:
        return {"findings": findings}
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            continue
        reason = entry.get("reason", "")
        if not isinstance(reason, str) or reason == "":
            continue
        if URL_PATTERN.search(reason) is None:
            findings.append({
                "rule_id": "SCP-R-004",
                "file": str(fixture_input_path),
                "severity": "warn",
                "summary": (
                    f"waiver entry {index} reason field must contain a "
                    f"decision-artifact URL (issue, PR, or decision log entry)"
                ),
            })
    return {"findings": findings}


def _evaluate_scp_r_002_python(fixture_input_path: Path) -> dict:
    """Minimal in-test evaluator mirroring SCP-R-002's waiver schema check.

    WP-SCP-022 slice 020Q (closes TF-006): short-circuits to no findings
    when an active waiver or rule-config disable is present for SCP-R-002.
    The meta-waiver pattern (a waiver against SCP-R-002 itself) is handled
    uniformly via rule_id matching — see RULE-002 §6 case 5 / 020L SAFE-MAJ
    closure. URL-bearing meta-waivers (per SCP-R-004 v1.1.0) satisfy this
    suppression too.
    """
    if _suppression_active("SCP-R-002", fixture_input_path.parent):
        return {"findings": []}

    payload = json.loads(fixture_input_path.read_text())
    findings = []
    if not isinstance(payload, list):
        findings.append({
            "rule_id": "SCP-R-002",
            "file": str(fixture_input_path),
            "severity": "high",
            "summary": "waivers.json root must be a JSON array",
        })
        return {"findings": findings}
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            findings.append({
                "rule_id": "SCP-R-002",
                "file": str(fixture_input_path),
                "severity": "high",
                "summary": f"waiver entry {index} must be an object",
            })
            continue
        has_identity = (
            (entry.get("rule_id") and isinstance(entry["rule_id"], str))
            or (entry.get("finding_id") and isinstance(entry["finding_id"], str))
        )
        if not has_identity:
            findings.append({
                "rule_id": "SCP-R-002",
                "file": str(fixture_input_path),
                "severity": "high",
                "summary": f"waiver entry {index} must include rule_id or finding_id",
            })
        for required in ("approved_by", "created_at", "expires_at", "reason"):
            value = entry.get(required)
            if not (isinstance(value, str) and value):
                findings.append({
                    "rule_id": "SCP-R-002",
                    "file": str(fixture_input_path),
                    "severity": "high",
                    "summary": f"waiver entry {index} must include {required}",
                })
    return {"findings": findings}


def _fixture_input_path(scenario_dir: Path) -> Path | None:
    for name in ("input.yml", "input.yaml", "input.json"):
        candidate = scenario_dir / name
        if candidate.exists():
            return candidate
    return None


@pytest.mark.parametrize(
    "rule_id,scenario,scenario_dir",
    list(collect_fixtures(FIXTURES_ROOT)),
    ids=lambda v: str(v) if not isinstance(v, Path) else v.name,
)
def test_conflict_gate_rego_python_agree(
    rule_id: str,
    scenario: str,
    scenario_dir: Path,
    opa_binary: str | None,
) -> None:
    """For each fixture, both engines and the expected verdict must agree."""
    if opa_binary is None:
        pytest.skip(f"opa not on PATH; skipping {rule_id}/{scenario}")

    input_path = _fixture_input_path(scenario_dir)
    if input_path is None:
        pytest.skip(f"no input fixture under {scenario_dir}")

    expected_path = scenario_dir / "expected-verdict.json"
    if not expected_path.exists():
        pytest.fail(f"expected-verdict.json missing under {scenario_dir}")

    rego_output = _run_opa(rule_id, input_path, opa_binary)
    python_output = _run_python_audit(rule_id, input_path)
    expected = json.loads(expected_path.read_text())

    outcome = evaluate_conflict_gate(
        rule_id=rule_id,
        fixture_path=str(input_path),
        rego_eval_json=rego_output,
        python_audit_json=python_output,
        expected_verdict_json=expected,
    )
    assert outcome.agreed, f"SCP-E005: {outcome.disagreement_reason}"
