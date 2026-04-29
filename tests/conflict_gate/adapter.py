"""Conflict-gate adapter for slice 020C.1.

Per WP-SCP-020 §4 020C.1 (iv): normalises Rego and Python evaluator
outputs to a unified `{rule_id, file, verdict, reason}` shape so the
CI job `rego-vs-python-conflict` can assert both engines agree.

Disagreement → SCP-E005 (per §4 020C.1 (iii)) → merge-blocked. The
unblock path is an amending decision in a separate PR that updates
the `expected-verdict.json` to match the now-ratified verdict.

This module is import-safe: it does NOT execute either engine. It
takes already-produced outputs and normalises. The CI job is
responsible for invoking OPA + the Python audit CLI separately.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

UnifiedVerdict = str  # "allow" | "deny"


@dataclass(frozen=True)
class UnifiedRecord:
    """Normalised verdict record produced from either engine."""

    rule_id: str
    file: str
    verdict: UnifiedVerdict
    reason: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "file": self.file,
            "verdict": self.verdict,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ConflictGateOutcome:
    """Result of comparing Rego, Python, and expected verdicts for a fixture."""

    rule_id: str
    fixture: str
    rego: UnifiedRecord
    python: UnifiedRecord
    expected: UnifiedRecord
    agreed: bool = field(init=False)
    disagreement_reason: str = field(init=False, default="")

    def __post_init__(self) -> None:
        agreed = (
            self.rego.verdict == self.python.verdict == self.expected.verdict
            and self.rego.rule_id == self.python.rule_id == self.expected.rule_id
        )
        # Use object.__setattr__ since dataclass is frozen
        object.__setattr__(self, "agreed", agreed)
        if not agreed:
            object.__setattr__(
                self,
                "disagreement_reason",
                (
                    f"verdict mismatch (rule_id={self.rule_id} fixture={self.fixture}): "
                    f"rego={self.rego.verdict}/{self.rego.rule_id} "
                    f"python={self.python.verdict}/{self.python.rule_id} "
                    f"expected={self.expected.verdict}/{self.expected.rule_id}"
                ),
            )


def normalise_rego_output(rule_id: str, fixture_path: str, rego_eval_json: Any) -> UnifiedRecord:
    """Normalise an `opa eval --format json --data <rule.rego> --input <input>` output.

    OPA's `--format json` returns a JSON object with shape:
      {"result": [{"expressions": [{"value": [<deny dict>, ...] | [], ...}]}]}
    A non-empty `value` array means deny; an empty array means allow.
    Each deny dict (per our rules) carries `{message, rule_id, file, ...}`.
    """
    if not isinstance(rego_eval_json, dict):
        return UnifiedRecord(
            rule_id=rule_id,
            file=fixture_path,
            verdict="allow",
            reason="rego output not a dict — treating as allow",
        )

    result = rego_eval_json.get("result", [])
    if not result:
        return UnifiedRecord(rule_id=rule_id, file=fixture_path, verdict="allow")

    expressions = result[0].get("expressions", []) if isinstance(result[0], dict) else []
    if not expressions:
        return UnifiedRecord(rule_id=rule_id, file=fixture_path, verdict="allow")

    deny_set = expressions[0].get("value", []) if isinstance(expressions[0], dict) else []
    if not deny_set:
        return UnifiedRecord(rule_id=rule_id, file=fixture_path, verdict="allow")

    # At least one deny; collect message of the first deny matching rule_id
    matching_denies = [
        d for d in deny_set
        if isinstance(d, dict) and d.get("rule_id") == rule_id
    ]
    if not matching_denies:
        # Deny found but for a different rule — still report deny with the first message.
        first = deny_set[0] if isinstance(deny_set[0], dict) else {}
        return UnifiedRecord(
            rule_id=rule_id,
            file=str(first.get("file", fixture_path)),
            verdict="deny",
            reason=str(first.get("message", "")),
        )

    first_match = matching_denies[0]
    return UnifiedRecord(
        rule_id=rule_id,
        file=str(first_match.get("file", fixture_path)),
        verdict="deny",
        reason=str(first_match.get("message", "")),
    )


def normalise_python_output(rule_id: str, fixture_path: str, audit_result_json: Any) -> UnifiedRecord:
    """Normalise SCP's audit-result JSON.

    The audit-result schema (`schemas/audit-result.schema.json`) carries
    `findings: [{rule_id, file, severity, summary, ...}]`. A finding for
    the given rule_id == deny; absence of any finding for that rule_id
    == allow.
    """
    if not isinstance(audit_result_json, dict):
        return UnifiedRecord(
            rule_id=rule_id,
            file=fixture_path,
            verdict="allow",
            reason="python output not a dict — treating as allow",
        )

    findings = audit_result_json.get("findings", [])
    matching = [
        f for f in findings
        if isinstance(f, dict) and f.get("rule_id") == rule_id
    ]
    if not matching:
        return UnifiedRecord(rule_id=rule_id, file=fixture_path, verdict="allow")

    first = matching[0]
    return UnifiedRecord(
        rule_id=rule_id,
        file=str(first.get("file", fixture_path)),
        verdict="deny",
        reason=str(first.get("summary", first.get("message", ""))),
    )


def load_expected_verdict(expected_path: Path) -> UnifiedRecord:
    """Load the canonical `expected-verdict.json` from a fixture directory."""
    payload = json.loads(expected_path.read_text())
    return UnifiedRecord(
        rule_id=str(payload["rule_id"]),
        file=str(payload.get("file", "")),
        verdict=str(payload["verdict"]),
        reason=str(payload.get("reason", "")),
    )


def evaluate_conflict_gate(
    rule_id: str,
    fixture_path: str,
    rego_eval_json: Any,
    python_audit_json: Any,
    expected_verdict_json: Any,
) -> ConflictGateOutcome:
    """End-to-end conflict-gate evaluation for one fixture."""
    rego = normalise_rego_output(rule_id, fixture_path, rego_eval_json)
    python = normalise_python_output(rule_id, fixture_path, python_audit_json)
    expected = (
        expected_verdict_json
        if isinstance(expected_verdict_json, UnifiedRecord)
        else load_expected_verdict(Path(expected_verdict_json))
        if isinstance(expected_verdict_json, (str, Path))
        else UnifiedRecord(
            rule_id=str(expected_verdict_json["rule_id"]),
            file=str(expected_verdict_json.get("file", "")),
            verdict=str(expected_verdict_json["verdict"]),
            reason=str(expected_verdict_json.get("reason", "")),
        )
    )
    return ConflictGateOutcome(
        rule_id=rule_id,
        fixture=fixture_path,
        rego=rego,
        python=python,
        expected=expected,
    )


def collect_fixtures(fixtures_root: Path) -> Iterable[tuple[str, str, Path]]:
    """Yield `(rule_id, scenario_name, fixture_dir)` for every fixture
    directory under `fixtures_root/<rule>/<scenario>/`."""
    if not fixtures_root.exists():
        return
    for rule_dir in sorted(fixtures_root.iterdir()):
        if not rule_dir.is_dir():
            continue
        rule_id = rule_dir.name
        for scenario_dir in sorted(rule_dir.iterdir()):
            if not scenario_dir.is_dir():
                continue
            yield rule_id, scenario_dir.name, scenario_dir
