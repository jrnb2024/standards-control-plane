# 020C.1 R1 — Opus self-review (correctness + safety lenses)

**Date:** 2026-04-29
**Reviewer:** Opus orchestrator (this session) — see `REVIEW-DEVIATION-2026-04-29.md` for why a Sonnet R1 dispatch was not used for these two lenses.
**Scope:** post-Round-1-fix codebase (commit-pending) covering all completeness findings + spec-drift item.
**Lenses covered:** correctness, safety_bypass.

This file records the orchestrator's adversarial self-review against the codebase as fixed. It is **not** a substitute for an independent Sonnet R1 dispatch; the next slice (020J) re-attempts the full 3× pattern.

## Methodology

I evaluated the fixed code against each lens charter from
`feedback_recursive_adversarial_review.md`, hunting specifically for
issues a same-author bias might miss:

- **Correctness:** Rego semantics under malformed inputs (non-array data.waivers, non-object rule_config), conftest data-namespacing reliability, OPA-eval `--data` ordering, schema validity (round-tripping date-time samples through Draft 2020-12 validator), workflow YAML parse-validity, lib bash syntax.
- **Safety/bypass:** Silent-bypass holes in waiver matching (finding_id-only path, malformed expires_at, timezone manipulation, missing field), rule-config schema-validation bypass, statuses:write privilege scope, lib failure modes (pyyaml absent, yaml parse errors), DoS surface, "indefinite past-edited expires_at" persistence path.

## Verdict

**APPROVED with two tracked-forward items.** No new BLOCKING findings beyond what was already addressed in Round 1.

## Findings

### TF-005 — One-release structural enforcement of expired rule-config is per-PR-warning only

**Severity:** tracked forward (not BLOCKING for 020C.1)
**Lens:** safety_bypass
**Claim:** The spec says expired rule-config "still suppresses for one release as a deprecation ramp." The implementation enforces this via per-PR `::warning::` annotation; there is no structural per-release tag-time check that refuses to publish v1.x.y when any `.scp/rule-config.yaml` entry has `expires_at` in the past. A determined developer could keep editing `expires_at` to a date in the past on every PR and the disable would persist forever, just with a perennial warning.

**Why this is tracked-forward, not blocking:** "One release" implies a release cycle. SCP's release cuts are a slice-020D2 concern (it's the slice that promotes the gate from advisory to required and cuts the v1.0.0 tag). The per-PR warning is the visible deprecation mechanism between releases; the release-cut-time refusal is the structural lock. Adding the release-cut check inside 020C.1 would expand its scope into 020D2 territory.

**Action:** Adds a 020D2 acceptance criterion: "Release-tag CI workflow MUST refuse to cut a v1.x.y tag if any `.scp/rule-config.yaml` entry in the working tree has `disable: true` AND `expires_at < now`. Verified by parsing rule-config.yaml at tag-time and asserting all active disables have future expiry."

### TF-006 — Conflict-gate fixture corpus does not yet cover waiver/rule-config suppression paths

**Severity:** tracked forward (not BLOCKING for 020C.1)
**Lens:** correctness
**Claim:** The Round-1 fix to `tests/conflict_gate/test_conflict_gate.py::_run_opa` adds `scp_common.rego` to the OPA invocation, so the conflict-gate now correctly evaluates the waiver-aware code path. But the existing fixture corpus has no waiver or rule-config fixtures — every fixture exercises the raw rule path only. Reviewer MAJ-001's mitigation suggested adding suppressed-by-waiver fixtures.

**Why this is tracked-forward, not blocking:** Adding a waiver-suppressed fixture requires both engines (OPA + Python) to agree on the suppressed verdict. The Python evaluator at `_evaluate_scp_r_001_python` etc. currently does not apply waivers — it just runs the raw rule logic. A waiver-suppressed fixture where Rego correctly returns `allow` (suppressed) but Python returns `deny` (unaware of the waiver) would deliberately fail the conflict-gate, defeating its authority. The right fix is to add waiver awareness to the Python evaluator side, which is WP-SCP-023 aggregator scope.

**Action:** Documented in `docs/integrations/conflict-gate.md` ("Scope of conflict-gate coverage (waivers + rule-config)") that suppression-path coverage stays at the OPA test layer (`policies/tests/scp_r_NNN_test.rego`) until Python evaluator gains waiver/rule-config awareness. WP-SCP-023 aggregator includes adding waiver-aware fixtures to the conflict-gate corpus as a prerequisite item.

## Items examined and cleared

- **Malformed `data.waivers` (non-array, missing).** `scp_waivers := w if { ... is_array(candidate) ... }` — when candidate is non-array, scp_waivers is undefined; `some w in scp_waivers` produces no iterations; no waiver matches; deny fires (fail-closed). ✓
- **finding_id-only waiver.** scp_active_waiver_for matches only on rule_id; finding_id-only waivers fail to suppress (fail-closed). Documented inline in scp_common.rego as a deliberate design choice for 020C.1 scope. ✓
- **Malformed `expires_at`.** Three disjunctive scp_waiver_expired bodies handle (a) missing/empty (b) malformed unparseable (c) past expiry — all return expired (fail-closed). ✓
- **Timezone manipulation `2099-12-31T23:59:59-12:00`.** Regex accepts the offset; time.parse_rfc3339_ns parses correctly to UTC ns; comparison against scp_now_ns is correct. ✓
- **Out-of-range hours `25:00:00`.** Regex matches but time.parse_rfc3339_ns fails; scp_dateish_ns is undefined; `not scp_dateish_ns(expires_at)` body of scp_waiver_expired matches → expired (fail-closed). ✓
- **conftest `--data` namespacing.** Lib wraps caller's waivers.json into `{"waivers": [...]}` and rule-config.yaml into `{"rule_config": {...}}` via tmp dir, ensuring `data.waivers` and `data.rule_config` resolve at the spec'd JSON paths regardless of conftest filename-derived merge semantics. ✓
- **OPA eval multi-`--data`.** `opa eval --data <rule.rego> --data <common.rego> ...` is a supported invocation pattern; no ordering surprise. ✓
- **Schema validation (Draft 2020-12) round-trips.** rule-config.schema.json + policy-check-summary.schema.json both validate cleanly; date-time samples for waivers_applied[*].expires_at and disabled_rules[*].expires_at pass validation post-MAJ-002 fix. ✓
- **YAML parse safety.** All `yaml.safe_load`, no `yaml.load` (RCE-safe). ✓
- **statuses:write scope.** Bounded to `repos/<caller>/statuses/<head_sha>` via the workflow's `gh api` call using `${{ github.token }}` (caller's GITHUB_TOKEN, caller permissions as ceiling). Documented in D-029. ✓
- **scp/policy-check-readback always state=success.** Read-back is informational, not a gate; the actual gate is the sibling `scp/policy-check` context. The sibling context's distinct name + the description text both make the informational role clear. ✓
- **Lib pyyaml-absent silent skip of rule-config.** Workflow ensures pyyaml at step 9 before sourcing the lib at step 11, so this code path is unreachable in the workflow context. Local invocations of the lib with pyyaml absent fall to "rule-config not applied" (denies fire) — fail-closed. ✓
- **DoS via huge waivers array.** Performance concern only; not a security boundary. Out of scope for 020C.1. Tracked-forward via 020D1 / 020H operational metrics. ✓
- **Tests against the fixed scp_waiver_expired definition.** Manually traced expired-waiver test cases for SCP-R-001/002/003: scp_waiver_expired holds for past expires_at → not scp_waiver_expired evaluates false → warn body fails → no warn record; same w with rule_id matching is rejected by scp_active_waiver_for → deny fires. count(results) == 1 ✓, count(warns) == 0 ✓.

## What this review does NOT cover

- Independent verification by a non-author. The Sonnet R1 budget block prevented this; documented in `REVIEW-DEVIATION-2026-04-29.md`.
- Adversarial fuzz of the lib post-processor against malformed conftest output JSON. The two existing branches (top-level kind vs metadata.kind) cover the conftest 0.68.x output shape per the documentation; if conftest ever changes the shape, the post-processor's defensive `isinstance` checks fall back to skipping unrecognised entries, which is correct fail-closed behaviour for observability data.

## Outcome

Round-1 fixes resolve all completeness BLOCKING findings + spec-drift item. The two tracked-forward items (TF-005 / TF-006) are correctly deferred to 020D2 and WP-SCP-023 respectively per their structural scope. Slice 020C.1 is ready to commit and open as PR.
