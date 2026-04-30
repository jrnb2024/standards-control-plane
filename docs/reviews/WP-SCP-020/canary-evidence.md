# Canary evidence — WP-SCP-020 federation primitive

**Initialised:** 2026-04-30 with slice 020E.a (pre-protection canary).
**Will be appended:** 020E.b (post-protection canary, post-020D2) and 020E.c (waiver-suppression canary).

This doc is the canonical audit trail for the three federation-primitive canaries that demonstrate the gate's deny + suppression behaviour. It is read by:
- `scripts/replay-canary.sh` (lands in 020E.c) — replays each canary against the current `@main` and `@v1.*` tags as part of weekly rollback-detection.
- The weekly scheduled workflow at WP-SCP-020 020H.1 iv-d — divergence from baseline opens a `rule-regression` issue automatically.

---

## Canary 1 — `canary/deliberate-violation-pre` (020E.a)

**Status:** ✅ Deny verified 2026-04-30 14:53 UTC.
**Branch:** `canary/deliberate-violation-pre` (preserved as a permanent fixture; do not delete).
**Branch SHA:** `1772a6b035488735cc4865fd16697027088cae33`.
**PR:** [#59](https://github.com/jrnb2024/standards-control-plane-/pull/59) — open with DO-NOT-MERGE label.
**Workflow run:** `25172373569`, job `73795068201` — [policy-check](https://github.com/jrnb2024/standards-control-plane-/actions/runs/25172373569/job/73795068201).
**Wall-clock (warm-start, binaries cached on runner):**
- Job started: 2026-04-30T14:53:38Z
- Job completed: 2026-04-30T14:53:58Z
- Total: **20 seconds**.
- Cold-start (first-time binary download + verify): not separately measured on this run; the workflow's `Resolve OPA + Conftest` step downloads + SHA256-verifies on every fresh runner. Estimated cold-start adds 10–15 s based on prior 020D1 runs.

### The deliberate violation

`services.yml` modified on the canary branch:

```yaml
- mode: mode.bearer_legacy
  deprecation_close_date: "2099-12-31"   # ← outside SCP-R-001 allowed set
  waiver_ref: scp-bearer-legacy-migration
```

The allowed set per SCP-R-001 is `{"2026-06-30", "2026-09-30"}`.

### Verdict

| Check | Result | Detail |
|---|---|---|
| `policy-check / scp/policy-check` | ❌ FAIL | exit code 1; SCP-E003 emitted |
| `scp/policy-check-readback` | ✅ pass | "2/3 rules enabled, 0 disabled, 1 not applicable" |

### Structured finding (from `policy-check-summary.json`)

```json
{
  "schema_version": "1.0.0",
  "pr_sha": "dd42b80ae9bc86f43087fbafbd99e4fbda905f03",
  "base_ref": "main",
  "rule_set": "starter",
  "workflow_run_id": 25172373569,
  "findings": [
    {
      "verdict": "deny",
      "rule_id": "SCP-R-001",
      "file": "services.yml",
      "path": "services.yml",
      "message": "services.scp.local.runtime_contract.auth_contract.accepted_modes[1].deprecation_close_date must be one of [\"2026-06-30\", \"2026-09-30\"] when mode=mode.bearer_legacy",
      "remediation_url": "https://github.com/jrnb2024/standards-control-plane-/blob/main/standards/service-lifecycle/SVC-003.md"
    }
  ],
  "disabled_rules": [
    {
      "rule_id": "SCP-R-003",
      "reason": "no-manifest-applicable",
      "expires_at": "2099-12-31"
    }
  ],
  "waivers_applied": [],
  "bypass_emitted": false,
  "conflict_gate": {
    "run": false,
    "disagreements": []
  }
}
```

### Why this is the right shape

- **The deny is structured** — `{rule_id, file, path, message, remediation_url}` — adopters can route findings to issue trackers, dashboards, scorecards.
- **The remediation URL points to the SVC-003 spec** — a reviewer (human or agent) clicking through gets the canonical authoritative document, not a generic CI failure page.
- **The message names the offending path inside the YAML** — `services.scp.local.runtime_contract.auth_contract.accepted_modes[1].deprecation_close_date` — so the reviewer sees exactly which line to fix.
- **`disabled_rules` correctly records SCP-R-003 as `no-manifest-applicable`** — the PR diff doesn't touch package.json/pyproject.toml/go.mod, so the rule emits an SCP-E006 observability record rather than a deny. Confirms the rule's adopter-friendly default-allow posture for non-manifest PRs.
- **`waivers_applied: []`** — the canary's `mode.bearer_legacy.waiver_ref: scp-bearer-legacy-migration` references a waiver that is NOT in the empty `output/findings/waivers.json`. So no suppression occurs, exactly as intended for the canary.
- **`bypass_emitted: false`** — `scp_bypass: true` is not set on the wrapper; the deny path is the natural outcome.
- **`conflict_gate.run: false`** — the conflict-gate workflow runs only on `pull_request` events touching `tests/conflict_gate/**` or related rule-engine paths; not on services.yml-only diffs.

### What this canary proves

The federation primitive's deny mechanism works on a real PR with a real violation. The mechanism is currently **advisory only** — `scp/policy-check` is not yet a required status check on `main` (slice 020D2 flips it). But the deny rendering, the structured finding payload, the schema validation, and the read-back commit-status all behave as specified.

---

## Canary 2 — `canary/deliberate-violation-post` (020E.b)

**Status:** ⏳ Pending — runs after slice 020D2 flips `scp/policy-check` to required.
**Expected outcome:** identical deny pattern to Canary 1, plus `mergeStateStatus: BLOCKED` (the required check actually blocks merge — vs the current "UNSTABLE" state where merge is technically allowed).

---

## Canary 3 — `canary/waived-violation` (020E.c)

**Status:** ⏳ Pending — runs after slice 020D2.
**Expected outcome:** `services.yml` deliberate violation on this branch is **suppressed** by a sibling `waivers.json` entry (in the same PR diff) with `expires_at` in the future. `waivers_applied[0]` carries the suppression record; `findings[]` is empty; `policy-check / scp/policy-check`: ✅ pass; `mergeStateStatus: CLEAN`.

---

## Replay procedure

`scripts/replay-canary.sh` (lands in 020E.c) replays all three canaries against the current `@main` and `@v1.*` tags. Divergence from this canonical baseline opens a `rule-regression` issue automatically (per WP-SCP-020 020H.1 iv-d weekly cron).

To replay manually pre-020E.c:

```bash
# Canary 1 — pre-protection deny
gh workflow run policy-check.yml --ref canary/deliberate-violation-pre
# Compare workflow output to the structured finding above. Any divergence is a regression.
```

## Tracked-forward observations

- **TF-E.a-001:** Cold-start vs warm-start wall-clock not separately measured on the 020E.a run (binaries were cached from prior 020D1 runs on the same runner pool). Resolution: add explicit cold-start measurement to `scripts/replay-canary.sh` when it lands in 020E.c (force-refresh runner cache; record both timings per replay).
