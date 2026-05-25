# RULE-003 — ACC-as-cross-repo-caller `allowed_callers` declaration

**Status:** DRAFT (operator-review surface; not yet UNDER REVIEW)
**Author:** @jrnb2024
**Filed:** 2026-05-24
**Target release:** v1.4.0 (SCP federation primitive).
**Type:** rule-add
**Quorum required:** 1 (single-operator mode per D-031)
**Review window:** 48h wall-clock from PR open.
**Bypass-surface non-empty:** `true` *(this rule extends `services.yml` with a new optional `allowed_callers` key + extends `.scp/rule-config.yaml` with `acc-cross-repo-caller-scoped: <bool>` opt-in flag for per-adopter ramp control. Adopters who set `acc-cross-repo-caller-scoped: false` (the default) suppress this rule entirely. The bypass surface is non-empty (the opt-in flag is a bypass), so the 48h review window is **non-waivable** per `README.md` — author cannot extend or shorten; zero approvals at 48h auto-defers. Closes WP-SCP-022 020H.1 R2 SAFE-MIN-001 pattern.)*

---

## 1. Summary

Add **SCP-R-006** at `threshold: warn` baseline in v1.4.0. The rule fires on PRs that modify the adopter's `services.yml` OR adopter's `<repo>/.acc/cross-repo-received-events.jsonl` audit log (the latter via a sibling rule path discriminator — see §3.1) on an adopter that has declared `acc-cross-repo-caller-scoped: true` in `.scp/rule-config.yaml`. When fired, the rule asserts that:

- (a) the adopter's `services.yml` declares `allowed_callers` as a non-empty list with at least one entry matching the canonical estate cross-repo caller registry at `control-tower/config/estate_repos.yaml`; AND
- (b) any MCP-server-spawn audit entries in `<repo>/.acc/cross-repo-received-events.jsonl` reference a `sender_acc_sa_uuid` matching the declared `allowed_callers` set (no orphan dispatches); AND
- (c) the per-repo MCP server source SHA at `<repo>/.acc/mcp_server.{py,ts}` matches the corresponding entry in the CT-published signed manifest (per D-036 Element 3).

Adopters opt out via `.scp/rule-config.yaml` `disable: true` with a justification + `expires_at`, identical to every other SCP-R-NNN rule. Adopters that do not declare `acc-cross-repo-caller-scoped: true` vacuously pass the rule — the rule guards itself against firing on adopters that have not opted in.

This is the first cross-repo-orchestration policy-layer rule, ratifying D-036 Element 1 (`services.yml` `allowed_callers` schema extension) + D-036 Element 3 (signed-manifest presence). It is deliberately the smallest viable rule: presence-only + audit-log-sender-match + manifest-SHA-pin, opt-in-per-adopter, warn-baseline. It does NOT verify JWT shapes in-flight, does NOT load the running MCP server subprocess, does NOT recompute the HMAC cosignal — those are runtime concerns of the target-repo's `ct-auth` verifier + acc-hook, not the SCP merge gate. Future rule proposals (RULE-004+) may add tighter cross-validation as evidence accumulates.

## 2. Motivation

### Real-world finding

ACC's EST-P plan-doc (`/Users/amplience/Projects/acc-est-p/docs/plans/PLAN-EST-P-cross-repo-orchestration-v3.md`) introduces a new auth pattern: ACC orchestrator dispatches WorkPackages to target estate repos via per-repo MCP server subprocesses, presenting an RS256 JWT scoped to the target repo's `app_id`. Per ESTATE-CONVERGENCE-CHECKPOINTS §43, no new auth mode may land in `services.yml` without going through the D-036 SCP rule-RFC vehicle. D-036 (filed as the companion ADR alongside this rule-RFC) ratifies the *shape* of the new auth pattern. RULE-003 / SCP-R-006 is the *enforcement* of that shape at the SCP federation gate.

The estate today has no machine-readable signal that a target repo's `services.yml` correctly declares its `allowed_callers`, that its on-disk MCP server source matches the canonical signed manifest, or that historical dispatches captured in the cross-repo audit log all reference known callers. An adopter could:

- Declare `allowed_callers: [acc]` in `services.yml` but ship a tampered MCP server source (Element 3 violation; SCP-R-006 catches via manifest-SHA-pin verification).
- Declare `allowed_callers: [some-typo-id]` (Element 1 violation; SCP-R-006 catches via registry cross-reference).
- Accept dispatches from a non-registered caller and the audit log captures the orphan dispatch (Element 1 + Element 4 violation; SCP-R-006 catches via audit-log sender-match).

Without SCP-R-006, the merge gate sees `services.yml` as just-another-YAML; the cross-repo caller pair shape D-036 commits to has no automated enforcement.

### Threat model / governance concern

Four failure modes the absence of SCP-R-006 enables:

1. **Caller-typo or stale-registry drift.** An adopter declares `allowed_callers: [acc-old]` or `[acc, deprecated-service]`. The dispatcher silently accepts dispatches from `acc` (which matches by audience) but the audit trail captures the literal declared list, not the canonical set. Over time, every adopter's `allowed_callers` drifts from `estate_repos.yaml`. Six months later when a new caller-pair audit is requested, the per-adopter declared sets do not converge to a single estate state. SCP-R-006 catches the drift at PR time: every `allowed_callers` entry must match a registered service in `estate_repos.yaml`.

2. **MCP server source tamper.** An adopter merges a PR that touches `<repo>/.acc/mcp_server.py` (e.g., to add a "convenience" tool). The CT-published signed manifest is not updated. ACC's `CrossRepoDispatcher` refuses to spawn the subprocess at runtime (Element 3's TOCTOU defence). But the source is in the tree; future operators may not realise the on-disk source is not the manifest-pinned source. SCP-R-006 catches at PR time: SHA-pin mismatch fires a finding.

3. **Orphan dispatch in audit log.** An adopter's `<repo>/.acc/cross-repo-received-events.jsonl` shows a dispatch event with `sender_acc_sa_uuid: <some-uuid>` that does NOT correspond to any registered ACC SA UUID. Either the dispatch is a stale residual from a pre-D-036 test (acceptable, but should be aged-out), OR an unregistered caller successfully presented a token (security incident). SCP-R-006 catches by cross-referencing every audit-log sender UUID against the canonical ACC SA registry; orphan dispatches surface as findings.

4. **Schema drift through silent forking.** An adopter copies an old `services.yml` template + adds custom `allowed_callers` keys that don't match the D-036 Element 1 schema (e.g., nested objects instead of a flat list). The custom shape passes `additionalProperties: false` if the schema isn't updated. SCP-R-006 + the runtime-contract schema extension (per D-036 §"Cross-references") jointly defend: SCP-R-006 evaluates the shape against the registered registry; the schema extension catches structural-shape violations at config-load.

### Prior conversation

- `docs/decisions/D-036-acc-cross-repo-caller-pair-2026-05-24.md` — the standalone ADR ratifying the SCP-side role in the ACC-as-cross-repo-caller auth pattern. RULE-003 is the implementation companion: D-036 Element 1 + Element 3 + the audit-trail discipline from Element 5 realised as a concrete rule proposal.
- `docs/ESTATE-CONVERGENCE.md` §43 — original "DO NOT add a new auth mode to services.yml without going through D-036 SCP rule-RFC" constraint. D-036 + RULE-003 jointly close that constraint.
- `/Users/amplience/Projects/acc-est-p/docs/plans/PLAN-EST-P-cross-repo-orchestration-v3.md` §3.5 + §4 + §15 SB-R2-003/007/008 — ACC-side parent plan-doc.
- `docs/home/HOME.md` §8.2 "Policy expansion" — names cross-repo orchestration as one of seven real candidates for the federation primitive to carry. RULE-003 is the second such candidate filed (after RULE-002 / DPBM).
- `docs/decisions/D-050-tf-pim-001-app-credential-surface-2026-05-21.md` — precedent for cross-repo authentication discipline; RULE-003 honours the same bounded-reversal + audit-trail-first posture.

## 3. Rule specification

### 3.1 Match conditions

The rule fires when ALL of the following hold for a PR:

1. The adopter's `.scp/rule-config.yaml` declares `acc-cross-repo-caller-scoped: true`. (Default is `false` or unset, in which case the rule does not fire — vacuous pass.)
2. EITHER (a) the PR's changed-files set contains `services.yml` (the canonical auth-declaration file), OR (b) the PR's changed-files set contains `<repo>/.acc/mcp_server.py` or `<repo>/.acc/mcp_server.ts` (any MCP server source change), OR (c) the PR's changed-files set contains `<repo>/.acc/cross-repo-received-events.jsonl` (audit-log append from a new dispatch arriving at PR-time — rare but possible during operator-attended demos). At least ONE of the three triggers must be present.
3. The adopter's repo tree at PR HEAD does NOT satisfy one or more of the following invariants (any unsatisfied invariant fires a separate finding):

    - **Inv-A (allowed_callers declared):** `services.yml`'s top-level service entry has `runtime_contract.allowed_callers` declared as a non-empty list of strings, each matching `^[a-z][a-z0-9-]*$`.
    - **Inv-B (allowed_callers registered):** every entry in `runtime_contract.allowed_callers` matches a `service_id` in `control-tower/config/estate_repos.yaml` (per D-036 §"Cross-references"). The registry is the closed set of known callers; unknown entries are findings.
    - **Inv-C (MCP server SHA-pinned):** if `<repo>/.acc/mcp_server.py` OR `<repo>/.acc/mcp_server.ts` exists in the tree, its SHA-256 (computed over the on-disk bytes) MUST match the corresponding entry in the CT-published signed manifest (per D-036 Element 3). The signed manifest is consumed read-only from a path the federation-primitive workflow knows (see §3.4 implementation sketch); SHA mismatch is a finding.
    - **Inv-D (audit log sender registered):** every entry in `<repo>/.acc/cross-repo-received-events.jsonl` (read as JSONL; one JSON object per line) MUST have a `sender_acc_sa_uuid` that matches the canonical ACC SA UUID registry. Orphan UUIDs are findings (one per orphan entry, capped at 10 to bound annotation noise; see §3.3).

Per D-036 §"Cross-references", the canonical ACC SA UUID registry lives in `control-tower/config/estate_repos.yaml`'s `services[].acc_sa_uuid` field (NEW field; see §3.4 schema extension). At v1.4.0 ship, this registry will have exactly one entry: ACC's single SA UUID across all 9 estate repos (per D-036 §"Decision points" item 5: shared key, single SA — and similarly, single UUID).

When all three (1), (2), AND (3) hold (with at least one unsatisfied invariant in (3)), emit one finding per unsatisfied invariant, with the finding's `path` field pointing to the offending file location.

Example: a PR on an `acc-cross-repo-caller-scoped: true` adopter that modifies `services.yml` to add `allowed_callers: [acc-typo]` (unregistered) triggers one finding for Inv-B, `path: services.yml`, severity `warn`.

### 3.2 Severity & threshold

- Initial threshold: **`warn`** per `policies/VERSIONING.md` — applies to Inv-A, Inv-B, Inv-D. New rules land at warn baseline; promotion to deny requires a separate rule-promote-warn-to-deny RFC (per D-036 process).
- **EXCEPTION: Inv-C fires at DENY immediately whenever the rule fires (per SB-MAJ-003 R1 fix).** Inv-C (MCP server SHA-pin against signed manifest) is a tamper-detection invariant — warn-baseline tamper detection is operationally meaningless because tamper is not a "rare false-positive ramp-up problem" but a binary security event. For any adopter who has set `acc-cross-repo-caller-scoped: true`, an Inv-C violation (on-disk MCP server source SHA does not match the CT-published signed manifest, OR the on-disk MCP server source is present but has no manifest entry) is treated as DENY regardless of `threshold-overrides` setting. Operationally: the per-adopter warn-to-deny ramp applies to Inv-A/B/D; Inv-C is always deny-on-fire.
- Adopter override: `.scp/rule-config.yaml` `disable: true` with `justification: <string>` and `expires_at: <date>` continues to suppress Inv-A/B/D (all three fields required by `schemas/rule-config.schema.json` — same shape as SCP-R-004 + SCP-R-005). **Inv-C is NOT subject to the `disable: true` waiver** — a tamper-detection invariant cannot be silenced by adopter declaration; the only legitimate response to an Inv-C finding is fixing the SHA mismatch (either by re-publishing the manifest with the new SHA, or reverting the MCP server source to match the manifest).
- Per-adopter promotion to deny: not via global RFC, but via the adopter setting `acc-cross-repo-caller-scoped: true` AND `threshold-overrides: { SCP-R-006: deny }` in their `.scp/rule-config.yaml`. Reuses the RULE-002-introduced `threshold-overrides` mechanism (the schema already supports it post-RULE-002; RULE-003 just adds `SCP-R-006` as a valid key per schema validation). Affects Inv-A/B/D only; Inv-C is always deny.
- **`threshold-overrides` value enum:** same `{warn, deny, disable, off}` set as RULE-002 §3.2. Migration parity preserved. Inv-C exemption is enforced in the Rego rule body (see §3.4) — `threshold-overrides: { SCP-R-006: disable }` suppresses Inv-A/B/D findings but NOT Inv-C.

The two-tier model (`acc-cross-repo-caller-scoped` boolean + `threshold-overrides` map) is necessary because the 9 cohort adopters reach EST-P-readiness on different timelines (per EST-P plan-doc §4.7 WS-EST-P-6 cohort cascade). RI is the first canary (per WS-EST-P-2); PIM, recommender, CT, SA, doc-agent, VS, FLA, shopify-app follow on their own clocks. A single global warn-to-deny ramp would either fire on under-ready adopters too soon or wait for the slowest. Per-adopter `threshold-overrides` is the natural shape, identical to RULE-002.

### 3.3 Annotation contract

- **Infrastructure error code** (annotation `title=`): `SCP-E003` for a deny finding, `SCP-E006` for a disabled-rule observability record. Same closed infrastructure-code set documented at ADOPT-001 §12.7.7. This rule does not introduce a new SCP-EXXX code.
- **Rule-specific annotation** (when `annotate=true`):
  - Inv-A: `::warning file=services.yml,title=SCP-R-006::ACC cross-repo caller pair: 'runtime_contract.allowed_callers' missing or empty — required for acc-cross-repo-caller-scoped: true adopter. See D-036 Element 1.`
  - Inv-B: `::warning file=services.yml,title=SCP-R-006::ACC cross-repo caller pair: 'runtime_contract.allowed_callers[i] = "<value>"' not in estate registry. Expected one of: [<registry contents>]. See estate_repos.yaml.`
  - Inv-C: `::warning file=.acc/mcp_server.py,title=SCP-R-006::ACC cross-repo caller pair: MCP server source SHA does not match CT-published signed manifest. Expected: <manifest-SHA>; got: <on-disk-SHA>. See D-036 Element 3.`
  - Inv-D: `::warning file=.acc/cross-repo-received-events.jsonl,title=SCP-R-006::ACC cross-repo caller pair: orphan sender_acc_sa_uuid '<value>' at line N — not in ACC SA UUID registry. See D-036 Element 1 + estate_repos.yaml.`
  - Annotation level escalates to `error` if the adopter has set `threshold-overrides.SCP-R-006: deny` per §3.2.
- The annotation deliberately carries D-036 + estate_repos.yaml cross-references inline. This is the failure-output remediation surface flagged by the adopter-experience perspective in D-049 §Rationale — a developer hitting this rule should see, in the PR Files-Changed tab, a direct pointer to the doctrine + registry they need to satisfy. *(URL forms resolve to the canonical published locations of D-036 + estate_repos.yaml; pending TF-D036-001-style canonical URL publication.)*
- Sibling `scp/policy-check-readback` commit-status text: "ACC cross-repo caller pair invariants failing (N findings)" — fits the ~80 char budget.
- **Inv-D annotation cap:** to bound annotation noise on a populated audit log, Inv-D emits at most 10 annotations per PR (the 10 oldest orphan entries — oldest because those are the longest-standing drift). A summary line "(...N additional orphan entries suppressed; see audit log)" appears as the 11th finding if N > 10. The cap is a render-side decision; the underlying Rego rule produces all findings, the workflow consumer truncates for annotation surface.

### 3.4 Implementation sketch

**Scope of this rule's v1.4.0 implementation slice:**

- **IN scope:**
    - `policies/SCP-R-006.rego` + tests covering all four invariants (Inv-A, Inv-B, Inv-C, Inv-D);
    - `scp_common.rego` helper additions: `jsonl_records` (parse JSONL input into list of objects), `manifest_lookup` (lookup entry in signed-manifest input by `target_repo_app_id`);
    - `schemas/rule-config.schema.json` extension for `acc-cross-repo-caller-scoped: <bool>` opt-in;
    - `schemas/runtime-contract.schema.json` extension for `allowed_callers: [<string>]` optional key (per D-036 Element 1);
    - `schemas/estate-repos.schema.json` (NEW) — schema for `control-tower/config/estate_repos.yaml`, declaring the `services[].acc_sa_uuid` field that Inv-D consults;
    - `schemas/cosignal-manifest.schema.json` (NEW) — schema for the CT-published signed manifest (per D-036 Element 3 — `schema_version: d-036-mcp-manifest-v1`);
    - `.github/workflows/policy-check.yml` narrow-glob input construction: materialise `services.yml` (already present), materialise `<repo>/.acc/cross-repo-received-events.jsonl` (NEW), materialise `<repo>/.acc/mcp_server.{py,ts}` SHA (NEW — workflow computes SHA, passes as `input.mcp_server_sha`), materialise CT-published signed manifest (NEW — fetched via SCP federation-primitive's existing trust-rooted Renovate cascade);
    - The SCP self-dogfood wrapper exercises the rule against SCP's own `main` — SCP itself is NOT `acc-cross-repo-caller-scoped: true` at v1.4.0 (SCP is not a target of ACC cross-repo dispatches), so the rule vacuously passes on SCP self-dogfood. Self-dogfood proves the rule loads + parses + emits no findings on a non-scoped adopter (a load-bearing test of the opt-in invariant);
    - `tests/conflict_gate/scp-r-006/{allow,deny}/` fixtures covering all four invariants;
    - `tests/conflict_gate/scp-r-006/{waiver-suppressed, waiver-expired, rule-config-disabled}/` suppression-path fixtures (mandatory per RULE-TEMPLATE §8).
- **OUT of scope for v1.4.0 (deferred to later rule-RFCs):**
    - JWT shape verification at PR-time (the rule does NOT parse historical JWTs from audit log; the audit log records `jwt_jti` not `jwt_full`. Shape verification is a runtime concern of the target's `ct-auth` verifier);
    - HMAC cosignal recomputation (Element 5 is a runtime concern; PR-time recomputation would require the HMAC key to be available to CI, which violates the kernel-protected key custody discipline);
    - Cross-validation of caller-side `outbound_callees` declarations (per D-036 §"Open questions" item 2 — the symmetric-declaration question is deferred to TF-D036-008 if it becomes load-bearing);
    - Token TTL ceiling verification (the verifier enforces it at receipt; PR-time evidence would require historical token timestamps which the audit log records, but cross-validating those against the dynamic TTL formula in D-036 Element 2 is a noisy heuristic for a marginal additional signal).
- **OUT of scope for v1.4.0 (deferred to v1.5.0+):**
    - Token-package distribution (D-049 Element 3 sibling — RULE-003 is the cross-repo orchestration analogue of RULE-002; the rule itself is the v1.4.0 deliverable, package distribution is a v1.5.0+ enhancement).

Proof-of-concept Rego pattern (lands separately under `policies/SCP-R-006.rego`, with companion tests under `policies/tests/scp_r_006_test.rego`):

```rego
package main

import data.scp_common as scp

scp_r_006_rule_id := "SCP-R-006"

# Adopter declared acc-cross-repo-caller-scoped via .scp/rule-config.yaml.
scp_r_006_acc_scoped if {
    object.get(input.rule_config, "acc-cross-repo-caller-scoped", false) == true
}

# Trigger paths the rule fires on (any one in the PR diff).
scp_r_006_trigger_paths := {
    "services.yml",
    ".acc/mcp_server.py",
    ".acc/mcp_server.ts",
    ".acc/cross-repo-received-events.jsonl",
}

scp_r_006_trigger_present if {
    some changed_file in input.changed_files
    some trigger in scp_r_006_trigger_paths
    glob_match(trigger, changed_file)  # helper in scp_common
}

# Canonical ACC SA UUID registry (closed list — at v1.4.0, one entry).
# Loaded from input.estate_repos_yaml by the workflow.
scp_r_006_known_acc_sa_uuids := {uuid |
    some service in input.estate_repos_yaml.services
    uuid := service.acc_sa_uuid
}

# Canonical service-id registry (the set of valid allowed_callers entries).
scp_r_006_known_service_ids := {service_id |
    some service in input.estate_repos_yaml.services
    service_id := service.service_id
}

# Inv-A — allowed_callers declared
scp_r_006_inv_a_finding contains finding if {
    not has_allowed_callers(input.services_yml)
    finding := {
        "rule_id": scp_r_006_rule_id,
        "severity": "warn",
        "path": "services.yml",
        "message": "ACC cross-repo caller pair: 'runtime_contract.allowed_callers' missing or empty — required for acc-cross-repo-caller-scoped: true adopter. See D-036 Element 1.",
        "invariant": "Inv-A",
    }
}

# Inv-B — allowed_callers entries are all in the estate registry
# Iterates the services dict (key, value) per CORR-MAJ-003 R1 fix —
# services.yml's `services:` is a mapping, not a list. The explicit
# `service_name, service` pair makes the dict shape explicit.
scp_r_006_inv_b_findings contains finding if {
    some service_name, service in input.services_yml.services
    some caller in service.runtime_contract.allowed_callers
    not caller in scp_r_006_known_service_ids
    finding := {
        "rule_id": scp_r_006_rule_id,
        "severity": "warn",
        "path": "services.yml",
        "message": sprintf("ACC cross-repo caller pair: 'services.%s.runtime_contract.allowed_callers' entry '%s' not in estate registry. See estate_repos.yaml.", [service_name, caller]),
        "invariant": "Inv-B",
        "service_name": service_name,
        "caller": caller,
    }
}

# Inv-C — MCP server source SHA matches manifest. SEVERITY: deny always
# (per SB-MAJ-003 R1 fix — tamper detection is binary, not ramp-able).
# Fires in two cases: SHA mismatch OR missing manifest entry for an
# on-disk MCP server. The second case closes CORR-MAJ-002 R1 fail-OPEN
# gap — without it, a missing-entry manifest passes vacuously.
scp_r_006_inv_c_findings contains finding if {
    input.mcp_server_path != ""
    expected := manifest_lookup(input.signed_manifest, input.target_repo_app_id)
    expected.mcp_server_sha256 != input.mcp_server_sha256
    finding := {
        "rule_id": scp_r_006_rule_id,
        "severity": "deny",
        "path": input.mcp_server_path,
        "message": sprintf("ACC cross-repo caller pair: MCP server source SHA mismatch. Expected %s; got %s. See D-036 Element 3.", [expected.mcp_server_sha256, input.mcp_server_sha256]),
        "invariant": "Inv-C",
    }
}

scp_r_006_inv_c_findings contains finding if {
    input.mcp_server_path != ""
    not manifest_has_entry(input.signed_manifest, input.target_repo_app_id)
    finding := {
        "rule_id": scp_r_006_rule_id,
        "severity": "deny",
        "path": input.mcp_server_path,
        "message": sprintf("ACC cross-repo caller pair: MCP server source present on disk but no entry in signed manifest for target_repo_app_id '%s'. See D-036 Element 3.", [input.target_repo_app_id]),
        "invariant": "Inv-C-missing-entry",
    }
}

# Inv-D — audit-log sender_acc_sa_uuid is in registry
scp_r_006_inv_d_findings contains finding if {
    input.audit_log_path != ""
    some record in jsonl_records(input.audit_log_contents)  # helper
    sender := object.get(record, "sender_acc_sa_uuid", "")
    sender != ""
    not sender in scp_r_006_known_acc_sa_uuids
    finding := {
        "rule_id": scp_r_006_rule_id,
        "severity": "warn",
        "path": input.audit_log_path,
        "message": sprintf("ACC cross-repo caller pair: orphan sender_acc_sa_uuid '%s' — not in ACC SA UUID registry. See estate_repos.yaml.", [sender]),
        "invariant": "Inv-D",
        "sender": sender,
    }
}

# Single aggregator rule (per CORR-MIN-003 R1 fix — replaces set-union
# syntax `|` with an explicit aggregator partial rule).
scp_r_006_all_ramp_findings contains finding if {
    scp_r_006_acc_scoped
    scp_r_006_trigger_present
    finding in scp_r_006_inv_a_finding
}

scp_r_006_all_ramp_findings contains finding if {
    scp_r_006_acc_scoped
    scp_r_006_trigger_present
    finding in scp_r_006_inv_b_findings
}

scp_r_006_all_ramp_findings contains finding if {
    scp_r_006_acc_scoped
    scp_r_006_trigger_present
    finding in scp_r_006_inv_d_findings
}

# Inv-C findings are NOT in the ramp set — they fire unconditionally
# at deny (per SB-MAJ-003 R1 fix). See deny rule below.

# Warn output — applies to Inv-A/B/D findings (the ramp-able invariants).
warn contains output if {
    some finding in scp_r_006_all_ramp_findings
    not scp_active_waiver_for(scp_r_006_rule_id)
    not scp_rule_config_disabled(scp_r_006_rule_id)
    not scp_threshold_override_deny(scp_r_006_rule_id)
    output := object.union(finding, {"msg": finding.message})
}

# Deny output — applies to ramp-able invariants when threshold-overrides
# sets deny, AND unconditionally to Inv-C findings (tamper detection).
deny contains output if {
    some finding in scp_r_006_all_ramp_findings
    not scp_active_waiver_for(scp_r_006_rule_id)
    not scp_rule_config_disabled(scp_r_006_rule_id)
    scp_threshold_override_deny(scp_r_006_rule_id)
    output := object.union(finding, {"msg": finding.message})
}

# Inv-C unconditional-deny (per SB-MAJ-003 R1 fix). Inv-C fires deny
# regardless of waiver, rule-config-disable, or threshold-overrides —
# tamper detection is binary, not ramp-able. NOTE: scp_r_006_inv_c_findings
# already carries severity=deny by construction.
deny contains output if {
    scp_r_006_acc_scoped
    scp_r_006_trigger_present
    some finding in scp_r_006_inv_c_findings
    output := object.union(finding, {"msg": finding.message})
}

# Helper — services.yml has at least one service with non-empty allowed_callers.
# Iterates the services dict (key, value) per CORR-MAJ-003 R1 fix.
has_allowed_callers(svcyml) if {
    some _, service in svcyml.services
    count(service.runtime_contract.allowed_callers) > 0
}

# Helper — manifest has entry for target_repo_app_id. NEW helper per
# CORR-MAJ-002 R1 fix (paired with manifest_lookup) — `manifest_has_entry`
# is true-when-defined; absence flips Inv-C's fail-OPEN → fail-CLOSED.
manifest_has_entry(manifest, target_repo_app_id) if {
    some entry in manifest.entries
    entry.target_repo_app_id == target_repo_app_id
}
```

Reused helpers from `policies/scp_common.rego`: `scp_active_waiver_for`, `scp_rule_config_disabled`, `scp_threshold_override_deny` (added by RULE-002), `glob_match` (added by RULE-002). New helpers needed: `jsonl_records(<string>) -> [<object>]`, `manifest_lookup(<manifest>, <target_repo_app_id>) -> <entry>`. Both add to scp_common per the rule-RFC implementation slice.

#### Implementation note — workflow-glob narrowing

Per the RULE-002 §3.4 precedent (workflow filters → Rego evaluates), the workflow narrows the inputs:

- `input.services_yml` — single-file load of `services.yml`.
- `input.changed_files` — existing per-PR diff list.
- `input.rule_config` — single-file load of `.scp/rule-config.yaml`.
- `input.mcp_server_path` + `input.mcp_server_sha256` — computed by the workflow if `.acc/mcp_server.{py,ts}` is present at HEAD. Empty string if absent.
- `input.audit_log_path` + `input.audit_log_contents` — `git show HEAD:.acc/cross-repo-received-events.jsonl` (if present; empty otherwise). Pre-truncated by workflow to the most recent 10,000 lines per Inv-D §3.3 annotation cap rationale (the rule fires on most-recent 10,000; older entries are out-of-scope for the gate even if present in the file — the audit log is meant to be append-only + archived/rotated externally).
- `input.estate_repos_yaml` — read from `control-tower/config/estate_repos.yaml`. Per D-036 §"Cross-references", SCP consumes this read-only via a manifest-published or vendored snapshot. The workflow fetches the most recent estate_repos.yaml from a pinned source (TBD — see §10 open question 1).
- `input.signed_manifest` — fetched via SCP federation-primitive's existing trust-rooted Renovate cascade (per D-036 Element 3); the CT-published manifest is updated whenever MCP server source SHAs change.
- `input.target_repo_app_id` — set by the workflow per the adopter's top-level `services.yml` service ID.

The narrow-glob discipline holds: every input is workflow-narrowed; Rego evaluates against bounded inputs, never crawling the working tree.

## 4. False-positive surface

Every rule has one. SCP-R-006 fires on legitimate manifests in the following cases:

1. **Adopter just declared `acc-cross-repo-caller-scoped: true` and is opening the first PR.** They have not yet committed `runtime_contract.allowed_callers`. The rule fires `warn` on Inv-A. Estimated FP rate: 1 per adopter per scope-declaration event (~9 total in WS-EST-P-6 cascade). Mitigation: the rule is `warn` baseline, not `deny`, so the PR is not blocked. Adopter can self-suppress for one release via `.scp/rule-config.yaml disable: true` with `justification: "first PR after acc-cross-repo-caller-scoped opt-in; allowed_callers declared in follow-up PR"` and `expires_at: <one release>`.

2. **Adopter is mid-rotation of an ACC SA UUID.** The audit log contains historical entries with the OLD SA UUID; the new entries reference the NEW SA UUID. Inv-D fires on the historical entries. Estimated FP rate: low (1-2 events per estate-wide SA rotation, which is rare). Mitigation: the audit log is append-only by design; rotation events emit a sentinel record (e.g., `{"event": "sa_uuid_rotation", "old_uuid": "...", "new_uuid": "...", "ts_utc": "..."}`) and SCP-R-006 §3.4 implementation slice extends `jsonl_records` helper to recognise the sentinel + treat all entries with `ts_utc < rotation_ts` as "rotation-legacy" and exempt their old UUID from Inv-D. Tracked-forward TF-RULE-003-001.

3. **MCP server source change without same-PR manifest update.** An adopter authors a PR that updates `<repo>/.acc/mcp_server.py` but does not include the corresponding manifest update in the same PR. **Per R2 obs 6 fix: Inv-C is now unconditional-deny (per §3.2 exception); this means same-PR manifest update is MANDATORY, not nice-to-have.** D-036 Element 3 "in the same PR or in a tightly-coupled follow-up PR" wording is superseded by the unconditional-deny enforcement at the SCP-R-006 level: MCP server source change PRs that omit the manifest update will block on Inv-C deny. Estimated FP rate: zero (the rule's enforcement IS the discipline). Mitigation: adopter MUST author MCP server source changes with manifest update in the same PR; alternative would require explicit rule-config-disable, but Inv-C is exempt from `disable: true` waiver per §3.2. The only escape hatch is a sibling RULE-RFC promoting Inv-C back to ramp-able OR an operator-attended emergency bypass via the `scp_bypass: true` three-gate model — both are operator-attended ceremonies, not adopter-side workarounds. This operational impact is the load-bearing trade-off of treating tamper detection as binary; the alternative (warn-baseline tamper) was rejected per SB-MAJ-003 R1 fix.

4. **Audit log contains entries from pre-D-036 testing.** Pre-EST-P-WS-EST-P-2 development may have generated `cross-repo-received-events.jsonl` entries with placeholder UUIDs. Inv-D fires on these. Estimated FP rate: per-cohort-adopter on first cascade install (9 total, one-shot). Mitigation: the install ceremony for the per-repo MCP server (per EST-P plan-doc §4.3 WS-EST-P-2.3) clears or archives any pre-existing audit log; subsequent dispatches start the log fresh with canonical UUIDs.

5. **estate_repos.yaml is out-of-date relative to the adopter's `services.yml`.** An adopter declares `allowed_callers: [acc]` but `estate_repos.yaml`'s pinned snapshot in SCP's workflow input doesn't include `acc`. Inv-B fires. Estimated FP rate: per-estate_repos.yaml-version-skew event (rare; mitigated by the Renovate cascade keeping the snapshot fresh). Mitigation: SCP's workflow uses a pinned `estate_repos.yaml` SHA; on cascade refresh, the new SHA is propagated. Adopters experiencing the FP can self-suppress via `disable: true` for a release with `justification: "estate_repos.yaml snapshot lag pending Renovate cascade"`.

## 5. Bypass surface

This rule introduces bypass-surface elements that make the 48h review window non-waivable. Enumerating them explicitly:

1. **`.scp/rule-config.yaml` `acc-cross-repo-caller-scoped: <bool>`** — new key. Default `false` (unset). When `false` or unset, SCP-R-006 does not fire. Adopters opt into cross-repo caller-pair enforcement by setting this key to `true`. The schema extension lives in `schemas/rule-config.schema.json`. **Bypass-by-omission discipline:** an adopter MUST NOT receive cross-repo dispatches without setting this key to `true`; the install ceremony (per D-036 Sequencing step 5: "RI declares `allowed_callers: [acc]` in mapp-returns-intelligence/services.yml") makes setting this flag part of the cascade discipline. Adopters who receive cross-repo dispatches without this flag are in an OFF-MAP state that the install-ceremony script SHOULD refuse; SCP-R-006 cannot enforce that runtime invariant but the rule-RFC names the expectation explicitly.

2. **`services.yml` `runtime_contract.allowed_callers: [<string>]`** — new optional key (per D-036 Element 1). When present and non-empty, restricts which peer services may present credentials to this service. When absent, the auth contract behaves as today (no peer-service restriction beyond auth mode). The schema extension lives in `schemas/runtime-contract.schema.json`. **Bypass-by-omission discipline:** an adopter who has `acc-cross-repo-caller-scoped: true` but does NOT have `allowed_callers` declared in `services.yml` triggers Inv-A — the rule's failure mode catches the omission, fail-loudly not fail-silently.

3. **`.scp/rule-config.yaml` `threshold-overrides: { SCP-R-006: <warn|deny|disable|off> }`** — reuses the RULE-002-introduced threshold-overrides shape. Adopters override the rule's global threshold per their `.scp/rule-config.yaml`. This is the per-adopter warn-to-deny ramp mechanism per §3.2. The schema validation is identical to RULE-002 §5 key 3.

**Implicit exclusion set (per RULE-TEMPLATE §5 SAFE-MAJ-002):** under what manifest shapes does this rule return `allow` (pass)?

- `acc-cross-repo-caller-scoped: false` (or unset) → rule vacuously passes regardless of `services.yml` shape. This is the dominant exemption — at v1.4.0 ship, no adopter has the flag set, so the rule produces zero findings estate-wide.
- `acc-cross-repo-caller-scoped: true` BUT the PR does not touch any trigger path (per §3.1 condition 2) → rule does not evaluate. This is the routine pass-through: an adopter that has opted-in continues to pass through PRs that do not touch the rule's scope.
- `acc-cross-repo-caller-scoped: true` AND trigger path touched AND all four invariants satisfied → rule passes (no findings emitted).
- `acc-cross-repo-caller-scoped: true` AND trigger path touched AND invariants violated BUT `disable: true` waiver present with valid `justification` + `expires_at` → rule emits `SCP-E006` observability record; no warn/deny.

The exemption set is intentional: opt-in-per-adopter mirrors the RULE-002 pattern + the cohort cascade's per-adopter clock. The bypass-by-omission discipline catches the "adopter is in the cascade but forgot to declare allowed_callers" case via Inv-A.

**Residual known bypass (per RULE-TEMPLATE §5):** SCP-R-006 enforces structural shapes (allowed_callers presence, registry membership, manifest SHA pin, audit log sender membership). It does NOT enforce semantic intent — e.g., a malicious adopter could:

- Add an attacker-controlled service_id to `estate_repos.yaml` AND declare that service_id in `allowed_callers`. SCP-R-006 sees a valid registry-member declaration. Closure path: `estate_repos.yaml` is in `control-tower/config/`, under control-tower CODEOWNERS (per D-031 single-operator-mode); adding a new entry requires a control-tower PR under operator review. The honest-actor posture accepts this residual; if operator account compromise is the threat model, that's a D-031 escalation concern not a RULE-003 concern.
- Tamper with `<repo>/.acc/mcp_server.py` AND the corresponding signed manifest entry. SCP-R-006 sees matching SHAs (manifest also tampered). Closure path: the signed manifest is signed with an Ed25519 key whose custody is CT-side (per D-036 Element 3 + §"Decision points" item 3); manifest signature verification (which the workflow performs before consuming the manifest) catches tamper. SCP-R-006 itself does not perform the signature verification; the workflow does — the rule consumes the verified manifest.

Both residuals are named explicitly so reviewers approving on `Bypass-surface non-empty: true` understand the rule's enforcement boundary: it asserts the *declared and audit-recorded shapes match the canonical registry and the verified manifest*, not the semantic intent of the registry or the manifest's signing key.

## 6. Conflict-gate strategy

How will this rule's Rego implementation be cross-checked against the Python evaluator?

- The rule's match conditions are expressible in the Python evaluator today: dict lookup on parsed YAML for §3.1 (1) + (2); list-membership tests for Inv-A/Inv-B; SHA256 comparison for Inv-C; line-by-line JSONL parse + dict lookup for Inv-D. No new evaluator primitives needed.
- Conflict-gate fixtures land at `tests/conflict_gate/scp-r-006/`:
  - `allow/` — adopter not scoped (1 fixture); adopter scoped but no trigger paths (1); adopter scoped + all invariants satisfied (1 per invariant × 4 = 4).
  - `deny/` — adopter scoped + each invariant violated separately (4 fixtures); adopter scoped + multiple invariants violated together (1 fixture).
  - `waiver-suppressed/` — adopter scoped + Inv-A violated + active waiver (1).
  - `waiver-expired/` — adopter scoped + Inv-A violated + expired waiver (1).
  - `rule-config-disabled/` — adopter scoped + Inv-A violated + `disable: true` (1).
  Total: 14 fixtures.
- A conflict-gate disagreement at runtime emits `SCP-E005` and merge-blocks (per ADOPT-001 §12.7.7). The proposer confirms the rule's fixtures will not cause the conflict-gate job to flap on the SCP self-dogfood gate before merge — SCP self-dogfood passes because SCP is not `acc-cross-repo-caller-scoped: true`.

## 7. Estate-cascade considerations

- Which estate adopters are likely to opt into this rule immediately at `warn`?
  - **RI (mapp-returns-intelligence):** First canary per EST-P plan-doc §4.3 WS-EST-P-2. Opts in concurrent with ACC WS-EST-P-2 ship.
  - **PIM (mapp-pim):** Second per WS-EST-P-6 cascade; gated on PIM main re-enabling `policy-check / scp/policy-check` required-check post-TF-PIM-001 (per D-050 §Sequencing Wave H).
  - **CT (control-tower), recommender, SA (mapp-size-allocation):** Third tier per WS-EST-P-6 cohort cascade; operator clock.
  - **mapp-doc-agent, mapp-visual-shopping, fashion-labelling-agent, shopify-app:** Fourth tier per WS-EST-P-6.
- Which are likely to need a transition period? All 9 cohort adopters need a 1-PR transition window between "first opt-in declaration" and "all invariants satisfied" (per FP case 1). Mitigated by `disable: true` waiver with `expires_at: <one release>`.
- Is there an estate-wide D-NNN forward-looking decision that should be filed in coordination with this proposal? Yes — D-036 (the companion ADR), filed at the same PR.

## 8. Test plan

- **Conftest test fixtures** (`policies/tests/scp_r_006_test.rego`): one test case per invariant × {satisfied, violated} = 8 cases. Plus opt-in test (acc-cross-repo-caller-scoped false → no findings). Plus trigger-path tests (no trigger → no findings; each trigger present → evaluates).
- **Conflict-gate fixtures** — both raw paths AND suppression paths per `docs/integrations/conflict-gate.md` §"Fixture authoring checklist":
  - Raw paths: `tests/conflict_gate/scp-r-006/{allow,deny}/` (14 fixtures per §6).
  - Suppression paths (mandatory when the deny body contains `not scp_active_waiver_for(...)` or `not scp_rule_config_disabled(...)`):
    `tests/conflict_gate/scp-r-006/{waiver-suppressed, waiver-expired, rule-config-disabled}/` with sibling `waivers.json` / `.scp/rule-config.yaml` files.
- **Workflow-selftest harness coverage** (`tests/workflow/scp-r-006-fixture/`): full workflow round-trip with services.yml + mcp_server.py + audit log + signed manifest + estate_repos.yaml inputs.
- **Canary update** — RI canary branch exercises the rule end-to-end at v1.4.0 ship.

## 9. Migration / rollout

Map onto `policies/VERSIONING.md` semver categories:

- New rule at `warn` → MINOR bump v1.4.0.
- Schema extensions (`runtime-contract.schema.json` `allowed_callers`; `rule-config.schema.json` `acc-cross-repo-caller-scoped`; `estate-repos.schema.json` NEW; `cosignal-manifest.schema.json` NEW) → MINOR bump (additive, no breaking changes to existing fields).
- Promotion to `deny` default → MAJOR bump after at least 3 adopters have operated at per-adopter deny for 6+ months. Tracked at TF-D036-005.

Target release: **v1.4.0**. Adopter-side migration steps (post-v1.4.0 Renovate cascade):

1. Adopter receives v1.4.0 SHA-pin bump via Renovate cascade. (No action required; rule does not fire on un-scoped adopters.)
2. When adopter is ready for cross-repo orchestration (per EST-P WS-EST-P-6 schedule), adopter sets `acc-cross-repo-caller-scoped: true` in `.scp/rule-config.yaml`.
3. Same PR (or tightly-coupled follow-up): adopter adds `allowed_callers: [acc]` to `services.yml`. Same PR: install ceremony script provisions `<repo>/.acc/mcp_server.{py,ts}` + `<repo>/.acc/credentials/cosignal-hmac-key`.
4. Adopter merges; SCP-R-006 fires at warn baseline (zero findings expected since invariants are satisfied by the install ceremony).
5. After ≥30 days of zero findings, adopter promotes to deny via `threshold-overrides: { SCP-R-006: deny }`.

## 10. Open questions

These are operator-amendment surfaces; mark each:

1. **`[deferrable]` — What source does the SCP federation-primitive workflow pull `estate_repos.yaml` from?** (Downgraded from `[BLOCKING]` to `[deferrable]` per CG-MAJ-002 R1 fix — the default is sound + low-stakes + the long-term build-artefact path is captured as TF-RULE-003-002.) Options: (a) vendored snapshot in SCP repo at `vendor/control-tower/estate_repos-<SHA>.yaml` (refreshed by Renovate); (b) live fetch from `control-tower/config/estate_repos.yaml` via raw.githubusercontent.com pin; (c) build artefact published by control-tower as a versioned release that SCP consumes via Renovate cascade. **Default if no response: option (a) vendored snapshot via Renovate.** Justifies because (b) introduces a runtime network dep at policy-check time which violates the federation primitive's "policy is statically evaluable against checked-out tree" invariant; (c) is the long-term ideal but pre-requires control-tower to ship the release artefact (out-of-scope for v1.4.0). Vendored snapshot via Renovate is the right v1.4.0 shape; the long-term build-artefact path is captured as TF-RULE-003-002.

2. **`[deferrable]` — Should Inv-D evaluate only the most-recent N entries in `cross-repo-received-events.jsonl`, or all entries?** §3.4 implementation slice proposes most-recent 10,000. Alternative: most-recent 1,000 OR all-entries with truncation only at annotation surface. Default if no response: most-recent 10,000 as proposed (bounds the Rego eval surface; archives are operator concern not gate concern).

3. **`[deferrable]` — Should Inv-C also verify the manifest's Ed25519 signature in Rego, or trust the workflow's pre-verification?** Default if no response: trust the workflow per the existing pattern (signature verification is the workflow's job; Rego consumes verified inputs). Captured as TF-RULE-003-003 if a later operator wants belt-and-braces signature check in Rego.

4. **`[deferrable]` — Does the `acc-cross-repo-caller-scoped` flag's default of `false` need a sentinel value (e.g., `null`) to distinguish "explicitly set to false" from "unset"?** Default if no response: NO — boolean semantics with default `false` is sufficient for the policy gate; sentinel distinction is captured as TF-RULE-003-004 if a later use case needs it (e.g., audit trail of explicit opt-out vs implicit unset).

## 11. References

- `docs/decisions/D-036-acc-cross-repo-caller-pair-2026-05-24.md` — companion standalone ADR; RULE-003 implements D-036 Element 1 + Element 3 + Element 5 audit-trail at the federation gate.
- `/Users/amplience/Projects/acc-est-p/docs/plans/PLAN-EST-P-cross-repo-orchestration-v3.md` §3.5 + §15 — ACC-side parent plan-doc.
- `/Users/amplience/Projects/control-tower/config/estate_repos.yaml` — canonical estate service registry consumed read-only by Inv-B + Inv-D.
- `docs/decisions/D-049-design-system-policy-layer-adoption-2026-05-19.md` + `docs/reviews/rule-proposals/RULE-002-dpbm-artefact-presence.md` — precedent rule-RFC + companion ADR pair; RULE-003 follows the same five-element shape, same `threshold-overrides` mechanism, same per-adopter ramp pattern.
- `docs/decisions/D-050-tf-pim-001-app-credential-surface-2026-05-21.md` — precedent for bounded-reversal posture under cross-repo authentication.
- `policies/SCP-R-005.rego` (when shipped) — closest pattern; RULE-003 implementation slice models SCP-R-006.rego on SCP-R-005's waiver-aware, rule-config-aware, warn-baseline shape.
- `policies/scp_common.rego` — helper library; this rule adds `jsonl_records`, `manifest_lookup` helpers.
- `schemas/rule-config.schema.json` — extends with `acc-cross-repo-caller-scoped` key.
- `schemas/runtime-contract.schema.json` — extends with `allowed_callers` optional key.
- `schemas/estate-repos.schema.json` — NEW; declares `services[].acc_sa_uuid` field that Inv-D consults.
- `schemas/cosignal-manifest.schema.json` — NEW; declares D-036 Element 3 signed-manifest schema.
- `docs/home/HOME.md` §8.2 — names cross-repo orchestration as one of seven real candidates for federation primitive policy expansion. RULE-003 is the second such candidate filed (after RULE-002 / DPBM).
- `docs/BACKLOG.md` Phase 12 → **TF-PIM-001** — explicit adopter-consumption-timing dependency. SCP-R-006 ships at v1.4.0 self-dogfood-only; external adopters cannot exercise the rule cross-repo until TF-PIM-001 Wave H closes. RULE-003 ships into the codebase independent of TF-PIM-001; *adopter consumption* is gated on it.

## Tracked-forward items (post-RULE-003 ratification)

- **TF-RULE-003-001 — Audit-log SA UUID rotation sentinel.** `jsonl_records` helper extension to recognise `{"event": "sa_uuid_rotation", ...}` sentinel records + exempt pre-rotation entries from Inv-D evaluation. Implementation slice when first SA rotation event occurs.
- **TF-RULE-003-002 — estate_repos.yaml long-term build-artefact distribution.** Per §10 question 1 default — long-term ideal is CT publishes estate_repos.yaml as a versioned release artefact; SCP consumes via Renovate cascade. v1.4.0 uses vendored-snapshot interim; the build-artefact path opens when CT has the publishing infrastructure (likely post-WP-AUTH-007).
- **TF-RULE-003-003 — Belt-and-braces Ed25519 manifest signature verification in Rego.** Per §10 question 3 default. Operator-decision when/if a future operator wants the additional defence-in-depth.
- **TF-RULE-003-004 — `acc-cross-repo-caller-scoped` sentinel distinction (`null` vs `false`).** Per §10 question 4 default. Trigger: a future use case needs to distinguish explicit opt-out vs implicit unset (e.g., audit of "which adopters consciously declined").
- **TF-RULE-003-005 — Inv-D annotation cap tuning.** Default 10 entries per §3.3. If operator evidence shows the cap is too tight (or too loose), tune in a sibling RFC.

---

**All `[BLOCKING]` open questions resolved by operator pre-restart authorisation pre-merge.** Proposal moves from operator-review-DRAFT to UNDER-REVIEW on PR-merge ceremony per the established rule-RFC review lifecycle.
