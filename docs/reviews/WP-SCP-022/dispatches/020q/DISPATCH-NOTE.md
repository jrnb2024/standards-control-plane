# WP-SCP-022 slice 020Q — conflict-gate suppression-path fixture corpus + Python waiver-awareness (dispatch note)

**Date:** 2026-05-02 (PM-4)
**Tier:** orchestrator-applied (Tier 1) per `feedback_four_tier_dispatch.md` — see "Tier-justification" below.
**Closes:** **TF-006** (primary — conflict-gate suppression-path fixture corpus per `project_020c1_tracked_forward.md`).
**Cuts:** no version bump. Internal-test surface only per `policies/VERSIONING.md` "Scope" — same posture as slices 020M / 020N / TF-020P-005 hash-pinning + tooling.

**Slice naming.** Letter `Q` is the next free post-Threshold-A letter after 020P (P-skipping convention only excludes `O`; `Q` is unambiguous in monospace). 020Q is a substantive standalone slice — meaningful new code surface (Python suppression-mirror helpers + OPA `--data` plumbing) plus new fixture corpus — not a TF-only closure.

## Rationale — why this slice now

Per `docs/reviews/WP-SCP-022/CONTINUATION-PROMPT-2026-05-02-pm-3.md` "Where the chain is" + the WP-SCP-023 sequencing dependency:

1. **TF-006 is gated on Python evaluator gaining waiver awareness.** Currently `tests/conflict_gate/test_conflict_gate.py::_evaluate_scp_r_NNN_python` does NOT consume sibling waivers.json or `.scp/rule-config.yaml`, while the Rego rules (via `policies/scp_common.rego`'s `scp_active_waiver_for` + `scp_rule_config_disabled` helpers) DO consume `data.waivers` + `data.rule_config`. Adding waiver/rule-config-suppressed fixtures today would deliberately fail the conflict-gate (Rego allow vs Python deny), defeating the gate's authority. The slice closes the gap by mirroring scp_common.rego's semantics in Python.
2. **WP-SCP-023 (cross-repo scorecards) is gated on TF-006.** TF-006 closure is the unblocker for the next-substantive-WP plan-doc + implementation work in this session.
3. **The Rego invocation `_run_opa` also lacks waiver/rule-config plumbing.** It currently invokes `opa eval --data <rule>.rego --data scp_common.rego --input <fixture-input>` without a `data.waivers` or `data.rule_config` source. To exercise the suppression code paths in scp_common.rego AT ALL, the invocation must learn to detect + load sibling `waivers.json` + `.scp/rule-config.yaml` files. This is the load-bearing OPA-side change — without it, the Rego rules silently fall through to the `default` predicates (no waivers, no rule-config disable) and the new fixtures would never exercise scp_common.rego's logic.
4. **All the existing rule files (SCP-R-001/002/004) already CALL the suppression helpers.** This slice does NOT touch policies/SCP-R-*.rego; the rules were authored 020C.1+ to consume the helpers. The slice fills the test-side gap.

## Scope decision — what's IN, what's OUT

### IN

| Item | Rationale |
|---|---|
| `tests/conflict_gate/test_conflict_gate.py` — new helpers: `_load_sibling_waivers`, `_load_sibling_rule_config`, `_scp_active_waiver_for`, `_scp_waiver_expired`, `_scp_rule_config_disabled`, `_parse_dateish_ns` | Mirror `policies/scp_common.rego` invariants 1:1. Each helper is a Python translation of the corresponding Rego rule. Comments cite the Rego source line for review trail. |
| `tests/conflict_gate/test_conflict_gate.py::_run_opa` — detect sibling `waivers.json` + `.scp/rule-config.yaml` in scenario_dir; combine into a tempfile dict `{"waivers": [...], "rule_config": {...}}`; pass as `--data <tempfile>` to opa eval | Without this, `data.waivers` / `data.rule_config` are undefined and Rego suppression always falls through to `default`. The new fixtures would never exercise the suppression paths. |
| `tests/conflict_gate/test_conflict_gate.py::_evaluate_scp_r_001_python` — apply `_scp_active_waiver_for("SCP-R-001", ...)` + `_scp_rule_config_disabled("SCP-R-001", ...)` short-circuit before findings emission | Mirror Rego suppression semantics for SCP-R-001. |
| `tests/conflict_gate/test_conflict_gate.py::_evaluate_scp_r_002_python` — same suppression check for SCP-R-002 | Mirror Rego semantics. **Subtlety:** SCP-R-002 is the meta-waiver rule — its OWN suppression check refers to "waivers against SCP-R-002", which is the meta-waiver pattern. The helper handles this uniformly via rule_id matching. |
| `tests/conflict_gate/test_conflict_gate.py::_evaluate_scp_r_004_python` — same suppression check for SCP-R-004 | Mirror Rego semantics. |
| `tests/conflict_gate/fixtures/SCP-R-001/waiver-suppressed/` — `input.yml` (bad mode) + `waivers.json` (active SCP-R-001 waiver, far-future expiry) + `expected-verdict.json` (allow) | Primary new corpus entry for waiver suppression. |
| `tests/conflict_gate/fixtures/SCP-R-001/waiver-expired/` — `input.yml` (bad mode) + `waivers.json` (waiver with EXPIRED `expires_at`) + `expected-verdict.json` (**deny**) | Fail-closed semantics: expired waiver does NOT suppress. Verifies both Rego and Python apply the same expiry semantics. |
| `tests/conflict_gate/fixtures/SCP-R-001/rule-config-disabled/` — `input.yml` (bad mode) + `.scp/rule-config.yaml` (disable: true for SCP-R-001) + `expected-verdict.json` (allow) | Primary new corpus entry for rule-config disable. Mirrors production layout (`.scp/` directory). |
| `tests/conflict_gate/fixtures/SCP-R-002/waiver-suppressed/` — bad waiver-shape input + meta-waiver suppressing SCP-R-002 + expected allow | Coverage for the meta-waiver pattern (RULE-002 §6 case 5 / 020L SAFE-MAJ). |
| `tests/conflict_gate/fixtures/SCP-R-004/waiver-suppressed/` — waiver-missing-URL input + meta-waiver suppressing SCP-R-004 + expected allow | Coverage for SCP-R-004 (warn-baseline) suppression. |
| `docs/integrations/conflict-gate.md` — §"Scope of conflict-gate coverage" updated to reflect the new fixtures + waiver-aware Python evaluator | The integration doc explicitly stated "raw rule paths only" pre-this-slice; update so adopters see the full coverage. |
| `STATUS.md` — TF-006 marked closed; "Today's chain (2026-05-02)" gets the 020Q row | Convention. |

### OUT

| Item | Rationale |
|---|---|
| Adding finding_id-level matching to `scp_active_waiver_for` (and the Python mirror) | Per scp_common.rego comment lines 36-43, finding_id correlation is deferred to WP-SCP-023's aggregator path where finding_ids are first-class. Maintaining "rule_id-only" parity preserves the documented fail-closed semantics. |
| Adding new SCP-R-NNN rules | Out of scope; this slice is suppression-path coverage only. |
| Modifying `policies/SCP-R-*.rego` or `policies/scp_common.rego` | All Rego-side suppression logic already exists since 020C.1. This slice is test-side only. |
| Refactoring `_evaluate_scp_r_NNN_python` into a shared base class | Three near-identical-shape evaluators COULD share more code, but the cost is a deeper class hierarchy that obscures the per-rule semantic distinctions. The duplication-with-comments-explaining-the-Rego-source pattern is intentional for review trail. |
| Adding `pytest.mark.parametrize` cases for the new helpers themselves (unit-testing the helpers in isolation) | The conflict-gate test framework IS the integration test for these helpers. A unit-test layer would add review surface without commensurate coverage value — every helper is exercised by at least one fixture's pass-path AND fail-path. |
| Adding rule-config `expires_at` parsing (per scp_common.rego comment "expired rule-config still suppresses for one release") | Rule-config expiry semantics deferred — `scp_rule_config_disabled` only checks `disable == true`. The "still suppresses for one release" warning emission is workflow-side (release-gate.yml), not test-side. Matching the workflow boundary. |
| `version-manifest.json` bump | Internal test surface only, no public-surface change. |
| `RELEASE_NOTES.md` entry | Internal test surface only. |
| New CODEOWNERS entry | Existing `tests/** @jrnb2024` (CODEOWNERS:36) covers the new test code; existing `docs/integrations/** @jrnb2024` covers the doc edit. No new entries required. |

## Tier-justification (why orchestrator-applied + 3-lens R1, NOT Codex executor)

Per `feedback_four_tier_dispatch.md` in-line escalation guidance:

**Arguments for Codex executor:** Multi-file change (~150 lines Python code + ~6 new fixture directories with multiple files each); semantic mirroring between two languages (Rego → Python) requires careful translation.

**Arguments for orchestrator-applied:**
- The Rego semantics are FULLY SPECIFIED in `policies/scp_common.rego` (104 lines, read end-to-end before authoring this DISPATCH-NOTE). Translation is mechanical: each Rego predicate → one Python function with the SAME boundaries.
- The fixture corpus is a small set of JSON/YAML files following an existing pattern (`tests/conflict_gate/fixtures/<rule_id>/{allow,deny}/` already established by 020C.1).
- The OPA `--data` plumbing change is a one-function addition (~20 lines).
- 3-lens R1 review is the right adversarial layer to catch semantic-translation bugs (correctness lens specifically focuses on Python↔Rego parity).
- All recent slices (020M / 020N / 020L / 020P / TF-020P-005) used orchestrator-applied + 3-lens R1 successfully. This slice has comparable surface; no design risk justifying the dispatch overhead.

**Decision: orchestrator-applied + 3-lens R1.** If R1 surfaces a CRIT/MAJ requiring non-trivial design rework (e.g. semantic divergence between Rego and Python that can't be reconciled by code edits), escalate to Codex executor for fix-round-2.

## Slice acceptance

- [ ] **(i) Helper functions exist.** `_load_sibling_waivers`, `_load_sibling_rule_config`, `_scp_active_waiver_for`, `_scp_waiver_expired`, `_scp_rule_config_disabled`, `_parse_dateish_ns` defined in `tests/conflict_gate/test_conflict_gate.py` with each function's docstring citing the matching Rego source location.
- [ ] **(ii) `_parse_dateish_ns` parses YYYY-MM-DD AND RFC3339.** Mirrors `scp_dateish_ns`. YYYY-MM-DD is treated as midnight UTC. Returns nanoseconds (or `None` for unparseable). Uses Python `datetime` (not third-party libs) for portability.
- [ ] **(iii) `_scp_waiver_expired` is fail-closed.** Missing/empty `expires_at` → expired (returns True). Unparseable `expires_at` → expired. `expires_at` ≤ now → expired. Matches `scp_waiver_expired` 3-clause Rego definition.
- [ ] **(iv) `_scp_active_waiver_for` matches rule_id only.** No finding_id matching (per scp_common.rego comment lines 36-43 deferring to WP-SCP-023). Iterates waivers; returns True iff any matching, non-expired entry exists.
- [ ] **(v) `_scp_rule_config_disabled` checks the exact path.** `rule_config["rules"][rule_id]["disable"] == True`. Returns False on missing key at any level (mirroring `default scp_rule_config_disabled := false`).
- [ ] **(vi) `_run_opa` detects + passes siblings.** If `<scenario_dir>/waivers.json` exists, load + add to data dict. If `<scenario_dir>/.scp/rule-config.yaml` exists, load + add. Combined dict → tempfile → `--data <tempfile>` argument. Tempfile cleaned up after invocation. Existing fixtures (allow/deny without siblings) continue to pass without modification.
- [ ] **(vii) Python evaluators apply suppression.** `_evaluate_scp_r_001_python`, `_evaluate_scp_r_002_python`, `_evaluate_scp_r_004_python` each load sibling waivers + rule-config, check suppression for their own rule_id, return `{"findings": []}` if suppressed (mirrors Rego's `not scp_active_waiver_for(...)` short-circuit). SCP-R-003 (no Python evaluator) unchanged.
- [ ] **(viii) Existing fixtures still pass.** No regression on `SCP-R-001/{allow,deny}/`, `SCP-R-002/{allow,deny}/`, `SCP-R-004/{allow,deny}/` after the helper additions.
- [ ] **(ix) New fixture: SCP-R-001/waiver-suppressed/.** input.yml has unapproved mode; waivers.json has active far-future SCP-R-001 waiver; expected-verdict.json says allow. Both engines produce allow.
- [ ] **(x) New fixture: SCP-R-001/waiver-expired/.** input.yml has unapproved mode; waivers.json has SCP-R-001 waiver with `expires_at` in the past (e.g. 2024-01-01); expected-verdict.json says **deny** (fail-closed).
- [ ] **(xi) New fixture: SCP-R-001/rule-config-disabled/.** input.yml has unapproved mode; `.scp/rule-config.yaml` has `rules.SCP-R-001.disable: true`; expected-verdict.json says allow.
- [ ] **(xii) New fixture: SCP-R-002/waiver-suppressed/.** input.json has malformed waiver shape; waivers.json has meta-waiver against SCP-R-002 (with URL-bearing reason per SCP-R-004 v1.1.0); expected-verdict.json says allow.
- [ ] **(xiii) New fixture: SCP-R-004/waiver-suppressed/.** input.json has waiver missing URL; waivers.json has meta-waiver against SCP-R-004; expected-verdict.json says allow.
- [ ] **(xiv) docs/integrations/conflict-gate.md updated.** §"Scope of conflict-gate coverage" reflects the new corpus. Closes the gap left by the previous "raw rule paths only" framing.
- [ ] **(xv) STATUS.md updates.** TF-006 marked closed (pointing at this slice). 020Q row added to "Today's chain (2026-05-02)" table.
- [ ] **(xvi) Adversarial review reaches fixpoint.** 3-lens R1 → recurse R2 / R3 until 0 new CRIT + 0 new MAJ on a complete cycle.
- [ ] **(xvii) PR opens + CI green + operator-merge per D-040.**
- [ ] **(xviii) Memory + STATUS backfill at close-out.** `project_020c1_tracked_forward.md` updated to mark TF-006 ✅ closed.

## Risk surface

1. **Semantic divergence between Rego and Python translations.** Specifically `_scp_waiver_expired`'s fail-closed branch handling. Mitigation: 3-lens R1 correctness specifically audits the Rego↔Python parity per helper.
2. **Tempfile cleanup in `_run_opa` may leak under exception.** Mitigation: use `tempfile.NamedTemporaryFile(delete=False)` with explicit `try: ... finally: os.unlink(path)` cleanup. Or `with tempfile.TemporaryDirectory(): ...` so cleanup is automatic.
3. **OPA `--data <tempfile>` namespace collision.** If the tempfile basename clashes with another data path, OPA's data tree could mis-merge. Mitigation: use a stable basename like `_scp_test_data.json` and inspect the dict structure post-load to verify `data.waivers` + `data.rule_config` resolve correctly.
4. **Date parsing edge cases.** RFC3339 datetime with timezone offsets vs UTC; daylight-savings ambiguity for naive datetimes. Mitigation: always interpret as UTC. Reject anything that doesn't match the regex (mirrors Rego's `regex.match` strictness).
5. **`yaml` module availability.** `_evaluate_scp_r_001_python` already imports yaml. `_load_sibling_rule_config` will too. If yaml is not installed, the suppression check skips (rule-config not found). Mitigation: yaml is in the test environment per existing imports.
6. **`pytest.mark.parametrize` test ID generation may collide for the new fixtures.** Mitigation: scenario directory names are unique within each rule_id (waiver-suppressed, waiver-expired, rule-config-disabled, etc.), so the parametrize IDs `SCP-R-001/waiver-suppressed` etc. remain distinct.
7. **Bypass-surface concern: could a tampered fixture corpus disable a rule's suppression check?** Mitigation: fixture changes route through CODEOWNERS `tests/** @jrnb2024` review; the suppression helpers themselves are tightly mirrored to scp_common.rego (review-trail in docstrings); existing test invariants (Rego/Python/expected three-way agreement) catch any silent-bypass attempt.
8. **Conflict with existing 020C.1 design.** Slice 020C.1 documented "raw rule paths only" as the intentional v1.0 scope to keep the conflict-gate landing tractable. This slice extends that scope. Mitigation: the new fixtures are ADDITIVE (they don't modify the existing allow/deny corpus); the docs/integrations/conflict-gate.md update calls out the scope expansion explicitly.

## R1 review

3× parallel Sonnet R1 (correctness / safety_bypass / completeness_governance). Recurse to fixpoint.

Review surface focuses:
- **Correctness.** Rego↔Python parity per helper; fail-closed semantics on `_scp_waiver_expired`; date parsing handles both formats; `_run_opa` tempfile + `--data` plumbing produces the expected `data.waivers` / `data.rule_config` namespaces; existing fixtures unbroken.
- **Safety/bypass.** No bypass surface introduced (could a malformed fixture trick an evaluator into silently allowing? could a path-traversal in waivers.json escape the scenario dir?); CODEOWNERS coverage of new files; tempfile cleanup under exception; no unsafe yaml.load (must be safe_load).
- **Completeness.** All 18 acceptance criteria in correct end-state; TF-006 closure attribution; new fixtures actually exercise scp_common.rego's branches (a fixture with no expected sibling but suppression-active would silently break parity); docs/integrations/conflict-gate.md update reflects the new state; STATUS.md "Today's chain" + TF-006 closure entry updated.

## Files

### Modified
- `tests/conflict_gate/test_conflict_gate.py` — new helpers + `_run_opa` plumbing + per-rule suppression checks.
- `docs/integrations/conflict-gate.md` — scope-of-coverage update.
- `STATUS.md` — TF-006 closure + 020Q chain row.

### Added
- `tests/conflict_gate/fixtures/SCP-R-001/waiver-suppressed/{input.yml, waivers.json, expected-verdict.json}`.
- `tests/conflict_gate/fixtures/SCP-R-001/waiver-expired/{input.yml, waivers.json, expected-verdict.json}`.
- `tests/conflict_gate/fixtures/SCP-R-001/rule-config-disabled/{input.yml, .scp/rule-config.yaml, expected-verdict.json}`.
- `tests/conflict_gate/fixtures/SCP-R-002/waiver-suppressed/{input.json, waivers.json, expected-verdict.json}`.
- `tests/conflict_gate/fixtures/SCP-R-004/waiver-suppressed/{input.json, waivers.json, expected-verdict.json}`.
- `docs/reviews/WP-SCP-022/dispatches/020q/{DISPATCH-NOTE.md, review-{correctness,safety,completeness}-package.json, review-{correctness,safety,completeness}.json, FIX-ROUND-N.md}`.

## Forward-looking

- **TF-020Q-001 candidate** (file at slice close if R1 surfaces it): if a 2nd warn-baseline rule is added (TF-020P-001 closure), `_evaluate_scp_r_NNN_python` for that rule will need its own suppression check — captured in the helper-reuse pattern established here.
- **Finding-id correlation** — deferred to WP-SCP-023 per scp_common.rego's documented note. Not in scope this slice.
- **Rule-config `expires_at` semantics** — workflow-side warn emission already exists (release-gate.yml). The Python suppression helper deliberately matches the Rego helper's "any disable == true" semantics; rule-config expiry warnings are not test-driven from conflict-gate fixtures.
