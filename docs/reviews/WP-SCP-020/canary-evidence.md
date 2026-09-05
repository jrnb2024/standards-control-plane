# Canary evidence — WP-SCP-020 federation primitive

**Initialised:** 2026-04-30 with slice 020E.a (pre-protection canary).
**Will be appended:** 020E.b (post-protection canary, post-020D2) and 020E.c (waiver-suppression canary).

This doc is the canonical audit trail for the four federation-primitive canaries that demonstrate the gate's deny + suppression behaviour. (Four canary verdicts; three distinct branches — canaries 1 and 2 share `canary/deliberate-violation-pre` per the §"Canary 2" strategy decision; canary 4 added at slice 020H.4 closing TF-020H1-004.) It is read by:
- `scripts/replay-canary.sh` (lands in 020E.c) — replays each canary against the current `@main` and `@v1.*` tags as part of weekly rollback-detection.
- The weekly scheduled workflow at WP-SCP-020 020H.1 iv-d — divergence from baseline opens a `rule-regression` issue automatically.

---

## Canary 1 — `canary/deliberate-violation-pre` (020E.a)

**Status:** ✅ Deny verified 2026-04-30 14:53 UTC.
**Branch:** `canary/deliberate-violation-pre` (preserved as a permanent fixture; do not delete).
**Branch SHA:** `1772a6b035488735cc4865fd16697027088cae33`.
**PR:** [#59](https://github.com/jrnb2024/standards-control-plane/pull/59) — open with DO-NOT-MERGE label.
**Workflow run:** `25172373569`, job `73795068201` — [policy-check](https://github.com/jrnb2024/standards-control-plane/actions/runs/25172373569/job/73795068201).
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
      "remediation_url": "https://github.com/jrnb2024/standards-control-plane/blob/main/standards/service-lifecycle/SVC-003.md"
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

**Status:** ✅ Verified 2026-04-30 (afternoon, post-020D2 + D-033 reconciliation).
**Strategy decision:** rather than open a *separate* `canary/deliberate-violation-post` branch (which would duplicate Canary 1's deliberate violation against an unchanged main), **020E.b reuses Canary 1's PR #59** as the post-protection witness. The canary branch was opened pre-020D2 and remained open through the 020D2 enforcement flip; it now sits in enforced-mode state with no rebase and no edit. This is structurally cleaner: the *same* deny that demonstrated advisory-mode rejection (Canary 1 / 020E.a) now demonstrates enforced-mode blocking (this section / 020E.b) without any new variable.

### What changed for PR #59 between 020E.a and 020E.b

| Property | Pre-020D2 (020E.a witness) | Post-020D2 + D-033 (020E.b witness) |
|---|---|---|
| `policy-check / scp/policy-check` | ❌ FAIL (advisory) | ❌ FAIL (required) |
| `mergeStateStatus` | `UNSTABLE` (merge technically allowed) | `BEHIND` (cannot merge under strict=true; rebase + still-failing-CI; admin override blocked by `enforce_admins=true`) |
| `mergeable` | `MERGEABLE` | `MERGEABLE` |
| Effective merge possibility | Operator could `gh pr merge --admin` | **Cannot merge** — `enforce_admins: true` blocks `--admin`; the deny is structural |

### Verdict

`gh pr view 59 --json mergeable,mergeStateStatus` returns `{"mergeStateStatus": "BEHIND", "mergeable": "MERGEABLE"}` post-020D2-apply. Attempting `gh pr merge 59` fails with `the base branch policy prohibits the merge`. The federation primitive's enforced-mode block is operational.

### Why "BEHIND" and not "BLOCKED"

GitHub's `mergeStateStatus` returns `BEHIND` whenever a PR's branch is not up-to-date with the base under `strict: true` required-status-checks. Even if the PR were rebased onto current main (closing the BEHIND), the rebase-rerun of CI would still fail because the deliberate violation (`deprecation_close_date: "2099-12-31"`) is the canary's whole point. Under enforcement: BEHIND collapses to BLOCKED on rebase; BLOCKED collapses to a permanent merge-block under `enforce_admins: true`. Effectively identical end-state.

### What 020E.b proves

Slice 020D2 actually enforces. The federation primitive isn't just *configured* to block; it *does* block, against the same canary that demonstrated the deny rendering pre-flip. Canary 1 + Canary 2 together establish the round-trip: deny works → enforcement makes deny binding.

---

## Canary 3 — `canary/waived-violation` (020E.c)

**Status:** ✅ Verified 2026-04-30 (evening, post-warn-msg-fix + wrapper-bump).
**Branch:** `canary/waived-violation` (preserved as permanent fixture, branch SHA `b4b1f5a` post-rebase).
**PR:** [#67](https://github.com/jrnb2024/standards-control-plane/pull/67) — open with DO-NOT-MERGE label.
**Workflow run:** `25175832144`, job `73807538507` — [policy-check](https://github.com/jrnb2024/standards-control-plane/actions/runs/25175832144/job/73807538507).
**Wall-clock:** 19 seconds (warm-start).

### The setup

Same deliberate SCP-R-001 violation as Canary 1 in `services.yml` (`deprecation_close_date: "2099-12-31"`), PLUS a sibling waiver entry in `output/findings/waivers.json` (in the same PR diff) targeting `rule_id: "SCP-R-001"` with `expires_at: "2099-12-31"`. Per WP-SCP-022 020C.1's waiver-aware Rego, the deny is suppressed and an observability `warn` record is emitted.

### Verdict

| Check | Result | Detail |
|---|---|---|
| `policy-check / scp/policy-check` | ✅ pass | Required check satisfied |
| `scp/policy-check-readback` | ✅ pass | "2/3 rules enabled, 0 disabled, 1 not applicable; 1 waiver(s) applied" |

### Structured finding (from `policy-check-summary.json`)

```json
{
  "schema_version": "1.0.0",
  "pr_sha": "620efa4ef638f196b429a67daec0e7d331ec1939",
  "base_ref": "main",
  "rule_set": "starter",
  "workflow_run_id": 25175832144,
  "findings": [],
  "disabled_rules": [
    {
      "rule_id": "SCP-R-003",
      "reason": "no-manifest-applicable",
      "expires_at": "2099-12-31"
    }
  ],
  "waivers_applied": [
    {
      "expires_at": "",
      "rule_id": "SCP-R-001"
    }
  ],
  "bypass_emitted": false,
  "conflict_gate": {
    "run": false,
    "disagreements": []
  }
}
```

### CI fixpoint #1 — warn records needed `msg`

The 020E.c canary's first run (workflow run `25175298908`) failed with conftest's: *"new result: 'msg' field must be present and a string"*. Pre-existing bug in the rule files: `warn` records emitted in 020C.1 lacked the `msg` field that conftest 0.x requires (the deny pattern was fixed via `object.union(finding, {"msg": ...})` but warn was overlooked). This was the first PR in SCP's history to actually exercise a real waiver-suppression path on a real PR diff — so the bug was masked everywhere else.

**Fix sequence:**

1. PR [#68](https://github.com/jrnb2024/standards-control-plane/pull/68) (`41a5299`) — added `msg` to all 6 warn records (2 per rule × 3 rules) + updated `policies/README.md` rule template so future rules don't reintroduce.
2. PR [#69](https://github.com/jrnb2024/standards-control-plane/pull/69) (`e67de09`) — bumped `policy-check-wrapper.yml` pin from `@9820489` to `@41a5299` so SCP-self picks up the fix.
3. Rebased `canary/waived-violation` onto new main (auto-includes the wrapper bump). Re-ran CI. Pass.

The fix is forward-compatible additive — external adopters pinned at `@9820489` keep working until they choose to upgrade.

### What this canary proves

The federation primitive's waiver-suppression mechanism works on a real PR with a real waiver. The structural triad (Canary 1 = deny advisory, Canary 2 = deny enforced, Canary 3 = deny suppressed) is now complete. Both deny + suppression paths verified end-to-end against real PR diffs under enforced mode.

### Tracked-forward observations

- **TF-E.c-001:** `waivers_applied[0].expires_at` reads as empty string `""` in the JSON summary, while the source waiver had `"expires_at": "2099-12-31"`. The warn record's `expires_at` field is set correctly in the rego rule; the post-processing step that projects warn records into the JSON summary is dropping the value. Resolution: post-Threshold-A audit of the JSON-summary projection step in `policy-check.yml`. Not blocking — the suppression behaviour works correctly; only the field-value display is affected.

---

## Canary 4 — `canary/rule-config-disabled` (020H.4)

**Status:** ✅ Suppress-via-rule-config verified 2026-05-01 10:32 UTC.
**Branch:** `canary/rule-config-disabled` (preserved as a permanent fixture; do not delete).
**Branch SHA:** `841d350f55c330258469f286328a8281b49bc28b`.
**PR:** [#81](https://github.com/jrnb2024/standards-control-plane/pull/81) — open with DO-NOT-MERGE label.
**Workflow run:** `25211284467`, job `73922292656` — [policy-check](https://github.com/jrnb2024/standards-control-plane/actions/runs/25211284467/job/73922292656).
**Wall-clock (warm-start):**
- Job started: 2026-05-01T10:32:43Z
- Total: ~17 seconds (warm-start; binary cache warm from prior runs).

### Why this canary

Per WP-SCP-020 020H.1 R1 SAFE-MIN-005 + TF-020H1-004: the existing canary corpus covered the deny path (canary 1) and the waiver-suppression path (canary 3), but NOT the `.scp/rule-config.yaml` `disable: true` suppression path. A regression in the rule-config-suppress logic (e.g. an `expires_at` handling bug, or a wrong-named-key parse drift) would not be caught by the weekly `canary-replay.yml` cron. This canary closes that gap as the third leg of the suppression-path coverage triad.

(Note: WP-SCP-020 plan §4 020H.1(iv)(d) names three canaries because the plan was frozen at Threshold A before TF-020H1-004 was filed. The plan doc is intentionally a historical snapshot; this canary-evidence.md is the live source of truth — TF-020H3-003 already covers the broader plan-doc-staleness issue.)

### The deliberate violation + suppression

`services.yml` carries the same deliberate violation as `canary/deliberate-violation-pre`:

```yaml
- mode: mode.bearer_legacy
  deprecation_close_date: "2099-12-31"   # ← outside SCP-R-001 allowed set
  waiver_ref: scp-bearer-legacy-migration
```

`.scp/rule-config.yaml` (force-added because `.scp/` is `.gitignore`d at the root for normal adopter workflow) carries SCP-R-001 disable:

```yaml
rules:
  SCP-R-001:
    disable: true
    justification: "WP-SCP-022 020H.4 canary fixture for the rule-config disable suppression path. Permanent canary branch; never merged. Closes TF-020H1-004."
    expires_at: "2099-12-31"
```

### Verdict

| Check | Result | Detail |
|---|---|---|
| `policy-check / scp/policy-check` | ✅ PASS | exit 0; deny suppressed by rule-config code path |
| `scp/policy-check-readback` | ✅ pass | "1/3 rules enabled, 1 disabled, 1 not applicable; SCP-R-001 until [empty] (rule-config override)" — see TF-E.c-001 (the `until [empty]` is the same `disabled_rules[*].expires_at` projection bug noted on canary 3, also affecting rule-config disable entries) |

### Structured finding (from `policy-check-summary.json`)

```json
{
  "schema_version": "1.0.0",
  "pr_sha": "fa4128988028961ea3a9aa7947ef58e8f02ccf04",
  "base_ref": "main",
  "rule_set": "starter",
  "workflow_run_id": 25211284467,
  "findings": [],
  "disabled_rules": [
    {
      "rule_id": "SCP-R-001",
      "reason": "rule-config override",
      "expires_at": ""
    },
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

### Discriminating signature vs Canary 3

The `replay-canary.sh` registry tuple discriminates the two suppression-path canaries:

| Canary | conclusion | findings | waivers_applied | disabled_rules |
|---|---|---|---|---|
| `canary/waived-violation` (Canary 3) | SUCCESS | 0 | **1** | 1 (SCP-R-003 only) |
| `canary/rule-config-disabled` (Canary 4) | SUCCESS | 0 | **0** | **2** (SCP-R-001 + SCP-R-003) |

The `waivers_applied` count is the primary discriminator: Canary 3 consumes a waiver (count=1); Canary 4 doesn't (count=0). The replay script's existing tuple shape (verdict + findings + waivers) catches a rule-config-suppress regression via the verdict + findings flip (a regression that breaks suppression makes the deny fire → conclusion=FAILURE + findings=1). The `disabled_rules` count is documented as a baseline observation but not used by the registry tuple — extending the tuple to include it is forward-compat (would catch a "disable still works but observability record dropped" regression class).

### Merge-protection note

PR #81 is **CI-green** (the `policy-check / scp/policy-check` required check PASSES because the rule-config disable suppresses the SCP-R-001 finding). Unlike Canary 1's PR #59, which is CI-FAIL and therefore structurally blocked by the required-status-check, **the only barrier preventing PR #81 from merging is the DO-NOT-MERGE label + operator discipline**. This matches Canary 3's PR pattern (also CI-green via waiver suppression). Bus-factor-1 risk: a single accidental click would merge any of the suppression-canary branches into main.

Forward-compat: when a second maintainer onboards (per D-031 escalation, 2026-07-21 review), add a Repository Ruleset matching `canary/*` that blocks merge to `main` from any `canary/` branch. Filed as TF-020H4-002.

### What this canary proves

The federation primitive's rule-config suppression mechanism works on a real PR with a real disable entry. The structural quad of detection canaries is now complete:

1. Deny advisory (Canary 1, 020E.a)
2. Deny enforced (Canary 2 — same branch, post-D-032)
3. Waiver-suppressed deny (Canary 3, 020E.c)
4. Rule-config-suppressed deny (Canary 4, 020H.4 — this section)

Both adopter-side suppression mechanisms (waivers + rule-config) are now exercised end-to-end against real PR diffs under enforced mode and watched by the weekly `canary-replay.yml` cron.

### Tracked-forward observations

- **TF-E.c-001 also affects this canary** — `disabled_rules[0].expires_at` reads as empty string `""` for the rule-config-override entry; the source rule-config had `expires_at: "2099-12-31"`. Same JSON-summary projection bug noted on Canary 3's waiver path. The suppression behaviour itself is correct; only the field-value display in the structured summary is affected. Resolution: post-Threshold-A audit of the JSON-summary projection step in `policy-check.yml` (pending).

---

## Replay procedure

`scripts/replay-canary.sh` (landed 2026-04-30 with this slice; extended in 020H.4 with the rule-config-disabled canary) replays all canary branches and asserts the verdict, findings count, and waivers-applied count against the canonical baseline. Output: tab-separated line per canary on stdout with `OK` or `REGRESSION (...)` per row. Exit code 0 if all OK; exit code 1 if any regression.

```bash
# Replay all canaries against the current main + v1.* tags.
./scripts/replay-canary.sh

# Force a fresh-runner cold-start measurement (TF-E.a-001).
./scripts/replay-canary.sh --measure-cold-start

# Override target repo (used in WP-SCP-024 estate cascade testing).
./scripts/replay-canary.sh --repo <other-owner>/<other-repo>
```

The 020H.1 weekly cron at `cron: "0 9 * * MON"` calls this script and opens a `rule-regression` issue if it exits non-zero. See `.github/workflows/rule-regression-detect.yml` (lands in slice 020H.1).

## Tracked-forward observations

- **TF-E.a-001:** Cold-start vs warm-start wall-clock not separately measured on the 020E.a run (binaries were cached from prior 020D1 runs on the same runner pool). Resolution: add explicit cold-start measurement to `scripts/replay-canary.sh` when it lands in 020E.c (force-refresh runner cache; record both timings per replay).
