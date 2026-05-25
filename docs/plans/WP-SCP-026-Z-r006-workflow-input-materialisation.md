# ProgrammePlan — WP-SCP-026-Z SCP-R-006 workflow-input materialisation (Codex Tier 2 dispatch)

**Work Package:** `WP-SCP-026-Z` (sibling slice to WP-SCP-026 MCP consumer integration; carries the kernel-dangerous workflow-extension half of D-036 RULE-003 / SCP-R-006 implementation that PR #148 explicitly carved out).
**Version:** 0.2 (DRAFT — 3-lens R1 plan-stage review folded; HALT at operator-attended first-fire).
**Status:** DRAFT — Z.1 WP-spec PR opened with 3-lens R1 R-FIXPOINT MET on v0.2. Z.2 Codex Tier 2 fire HELD for operator-attended authorisation post-merge.
**R-cycle changelog:**
- **v0.1 (2026-05-25 PM):** initial plan-doc + dispatch JSON authoring.
- **v0.2 (2026-05-25 PM):** 3-lens R1 plan-stage review fold. Lens A FIRE-WITH-FIXES (1 CRIT + 2 HIGH); Lens B APPROVED; Lens C REJECT (1 CRIT scope + 1 HIGH STATUS missing). All CRIT/HIGH folded into dispatch JSON v0.2 + plan-doc updated. Cure-worse trigger NOT invoked — mechanical/governance findings, not architectural; same disposition pattern as TF-PIM-001 Wave D'.1 v0.2 → v0.3 fold.
**Date kicked off:** 2026-05-25 (Phase Q of the 2026-05-25 PM session; operator-authorised under "all of them in order please" — Phase O bookkeeping + Phase P D-054 + Phase Q this WP-spec + Phase R 024E scaffolds).
**Owner:** operator (Tier 2 dispatch + R-cycle on impl; Codex executor on impl).
**Predecessors:**
- PR #148 (D-036 + RULE-003 / SCP-R-006 rule-RFC + ADR pair) — landed 2026-05-25.
- Phase G of this session (PR #155) — SCP-R-006 Rego impl shipped at v1.3.0; inputs vacuous-pass when absent (safe failure mode per the SCP-R-006.rego §"v1.4.0 ship scope" header).
- D-036 (ACC-as-cross-repo-caller pair ADR) — references the workflow extension as a separate slice.

**Companion ratification artefacts:** none new — this WP-spec inherits D-036 Element 1+2+3+4 ratification + RULE-003 §3.4 Implementation sketch authority. No new D-NNN. If the workflow-extension surface requires architectural deviation from RULE-003 §3.4, a sibling D-057+ may be filed inline; not anticipated at v0.1 authoring.

---

## 1. Purpose

SCP-R-006 (D-036 RULE-003) ships at v1.3.0 as Rego-only (`policies/SCP-R-006.rego` + tests; per-rule coverage 95.81%; merged via PR #155 at squash sha `c4bb830`-precursor). The rule body references 10 input keys that **the federation-primitive workflow (`.github/workflows/policy-check.yml`) does NOT yet materialise**. Per the SCP-R-006.rego header comment lines 14-26 + RULE-003 §3.4 §"IN scope" bullet "`.github/workflows/policy-check.yml` narrow-glob input construction" — the rule was deliberately landed *before* its workflow inputs to preserve safe-failure-mode discipline (rule loads but invariants vacuously pass when inputs absent).

This WP-spec is the **kernel-dangerous half**: extend the federation-primitive workflow to materialise the 10 input keys SCP-R-006 needs.

The 10 inputs SCP-R-006 reads (verbatim from `policies/SCP-R-006.rego` header lines 16-19):

| # | Input key | Source | Type |
|---|---|---|---|
| 1 | `input.services_yml` | adopter checkout: `services.yml` → `yaml.safe_load` | object |
| 2 | `input.changed_files` | gh PR diff list | array of strings |
| 3 | `input.rule_config` | adopter checkout: `.scp/rule-config.yaml` → `yaml.safe_load` | object |
| 4 | `input.mcp_server_path` | adopter checkout: detected path of `.acc/mcp_server.{py,ts}` if present | string |
| 5 | `input.mcp_server_sha256` | computed hash of file at `input.mcp_server_path` | string |
| 6 | `input.audit_log_path` | adopter checkout: detected path of `.acc/cross-repo-received-events.jsonl` if present | string |
| 7 | `input.audit_log_contents` | file contents at `input.audit_log_path` | string |
| 8 | `input.estate_repos_yaml` | cross-repo fetch from CT-published `control-tower/config/estate_repos.yaml` (per D-036 Element 4) | object |
| 9 | `input.signed_manifest` | cross-repo fetch from CT-published Ed25519-signed manifest path (per D-036 Element 3) | object |
| 10 | `input.target_repo_app_id` | adopter `.scp/rule-config.yaml` → `target-repo-app-id:` key (NEW schema extension) | string |

## 2. Goal + success criterion

**Goal:** SCP-R-006's four invariants (Inv-A allowed_callers-declared / Inv-B caller-in-registry / Inv-C MCP-server-SHA-matches-manifest unconditional-deny / Inv-D audit-log-orphan-detection) actually fire under the federation-primitive workflow against an opt-in adopter, instead of vacuously passing because the inputs are absent.

**Success criterion (verified at first-fire on SCP-self):**
- Workflow runs on a SCP-self PR with `.scp/rule-config.yaml { acc-cross-repo-caller-scoped: true }` set (a synthetic SCP-self opt-in for the fire test); a deliberately-corrupted `services.yml` (e.g. `allowed_callers: ["not-in-registry"]`) produces an Inv-B finding visible in the PR annotation; the SCP-self post-fire revert (clean PR) shows the rule passes; vacuous-pass on adopters without the opt-in still holds.
- Inv-C invariant fires unconditional-deny on a manifest-mismatch fixture (selftest harness).
- All existing rules (SCP-R-001 through SCP-R-008) continue to evaluate per-file as before (no regression in the per-file evaluation mode).

**Anti-criterion (treat as failed and re-scope if any of these hold post-fire):**
- Any existing per-file rule (SCP-R-001..005, R-007, R-008) regressed or had its per-file input shape mutated.
- The PR-level evaluation path leaks input values into per-file evaluations (cross-mode contamination).
- Cross-repo fetch of CT-published artefacts uses anything other than the established federation-primitive GitHub App credential surface (D-050 Path C v2) — no PATs, no `secrets: inherit` violations.

## 3. Architecture sketch

### 3.1 Evaluation mode separation

Conftest's current invocation in `lib/policy_check_invocation.sh:113-320` is **per-file**: each changed file becomes `input` to every rule. SCP-R-006 needs **PR-level** evaluation: a single composite `input` document per PR, evaluated once. Two viable shapes:

- **Option α (RECOMMENDED) — sidecar conftest invocation.** A second conftest invocation against the same policy bundle but against a synthesised single-file `pr-input.json` containing all 10 materialised keys. The first invocation (per-file) retains its current semantics; the second (PR-level) targets only rules that opt into PR-level evaluation. SCP-R-006 is the first PR-level rule; subsequent PR-level rules use the same harness. Findings from both invocations merge into the existing `policy-findings.json`.
- **Option β — per-rule registry of evaluation-mode + harness rebuild.** Introduce a `policies/EVALUATION_MODES.yaml` registry mapping rule IDs to `per-file` vs `pr-level` and rebuild the harness to honour the registry. Higher architectural surface; defers the SCP-R-006 fire by ≥1 sprint.

**This WP-spec selects Option α** (sidecar invocation). Lower architectural surface; preserves per-file rules unchanged; the second invocation is gated on detection of any PR-level rule in the policy bundle. If Option β becomes desirable later, the sidecar invocation refactors cleanly into the registry pattern.

### 3.2 Cross-repo fetch (D-050 Path C v2 reuse)

Inputs 8 + 9 require reading two files from the CT repo. The federation primitive's existing GitHub App credential surface (D-050 Path C v2, App `scp-federation-primitive`) is the trust-rooted path — but the App's `Repository access` is currently scoped to `jrnb2024/standards-control-plane` only (per D-050 §"App identity + scope"). Two sub-options:

- **Sub-option α.1 (RECOMMENDED) — CT publishes the artefacts to a public location consumable without App-token-exchange.** CT's existing public surface for `governance/docs/notifications/` is precedent; same posture for `governance/published/estate_repos.yaml` + `governance/published/cosignal-manifest.json` + their Ed25519 signatures. Reads via `gh api repos/jrnb2024/control-tower/contents/...` with `GITHUB_TOKEN` (caller's wrapper context; read-only). Signature verification happens *in* the policy-check job using a vendored CT public key (pinned in SCP-self `vendor/ct-cosignal-public-key.pem` + reviewed quarterly).
- **Sub-option α.2 — extend App `Repository access` to include `jrnb2024/control-tower`.** Requires App-install ceremony amendment + D-050 §"App identity + scope" amendment. Higher operator cost; lower trust-of-distribution risk (only SCP federation primitive can fetch).

**This WP-spec selects sub-option α.1** (public publish + Ed25519 verification in-job) — preserves the App's minimal-scope posture (D-050 §"App identity + scope") and matches the cosignal pattern's existing public verification surface (RULE-003 §3.4 references Element 3 as a published artefact).

### 3.3 Schema extensions

Three schema files require extension (all additive, content-addition non-kernel-dangerous):

1. **`schemas/rule-config.schema.json`** — extend with optional `target-repo-app-id: <string>` (matches the format CT publishes; required only when `acc-cross-repo-caller-scoped: true`).
2. **`schemas/estate-repos.schema.json`** (NEW; created by PR #148) — already defines `services[].service_id` + `services[].acc_sa_uuid`. No extension required.
3. **`schemas/cosignal-manifest.schema.json`** (NEW; created by PR #148) — already defines `entries[].target_repo_app_id` + `entries[].mcp_server_sha256`. No extension required.

### 3.4 Workflow change surface

`.github/workflows/policy-check.yml` receives a NEW STEP block under the existing `policy-check` job, AFTER the existing per-file conftest invocation step, BEFORE the existing readback step. The step block:

1. Detects whether the policy bundle contains any PR-level rule (initially: `grep -l "scp_r_006_" "${SCP_RUNTIME_ROOT}/policies/*.rego"`). If not, short-circuit (no extra work).
2. Constructs `pr-input.json` containing the 10 materialised inputs:
   - `services_yml`: yaml.safe_load of adopter `services.yml` (empty `{}` if missing).
   - `changed_files`: line-list from existing `changed-files.txt` (already constructed at line 677-690 of policy-check.yml).
   - `rule_config`: yaml.safe_load of adopter `.scp/rule-config.yaml` (empty `{}` if missing).
   - `mcp_server_path` + `mcp_server_sha256`: detect `.acc/mcp_server.py` then `.acc/mcp_server.ts`; if either present, compute SHA256 via `sha256sum`; if both present, prefer `.py` (per RULE-003 §3.1 trigger order). Empty strings if neither present.
   - `audit_log_path` + `audit_log_contents`: read `.acc/cross-repo-received-events.jsonl` if present; empty strings if not.
   - `estate_repos_yaml`: fetched via `gh api repos/jrnb2024/control-tower/contents/governance/published/estate_repos.yaml` then `yaml.safe_load`. If fetch fails (404 / network) — fail-CLOSED with SCP-E003 if the adopter opted in (`acc-cross-repo-caller-scoped: true`); vacuous-pass-OK if not opted-in.
   - `signed_manifest`: fetched via `gh api repos/jrnb2024/control-tower/contents/governance/published/cosignal-manifest.json` + companion `.sig` + Ed25519-verify in-job using vendored CT public key at `vendor/ct-cosignal-public-key.pem`. Same fail-CLOSED-when-opted-in / vacuous-pass-when-not posture.
   - `target_repo_app_id`: read from `input.rule_config["target-repo-app-id"]` if present + opted-in.
3. Invokes conftest a SECOND TIME against the same policy bundle but with `pr-input.json` as the single target file (sidecar invocation per §3.1). Output merges into `policy-findings.json` via the existing python aggregation block (line 322-345 of `lib/policy_check_invocation.sh`).

### 3.5 Out-of-scope (defer to later WP-spec)

- Multi-rule PR-level evaluation registry (`policies/EVALUATION_MODES.yaml` Option β path). Adopt when ≥2 PR-level rules exist.
- Caching of cross-repo fetches (estate_repos.yaml + signed manifest) across multiple PRs in the same workflow-run window. Single-fetch-per-job is acceptable at v1.4.0 scale.
- Receipt-signature TTL semantics on the cosignal manifest (D-036 Element 3 references but does not specify; defer to TF-D036-MANIFEST-TTL-001 if it becomes load-bearing).
- ACC-side cosignal HMAC verification (D-036 Element 5; runtime concern, not PR-time).

## 4. Slice plan (single Codex Tier 2 dispatch)

| Slice | Deliverable | Tier |
|---|---|---|
| Z.1 (this WP-spec) | DRAFT PR opening this plan-doc + the dispatch JSON. 3-lens R1 plan-stage review (sec / arch-skeptic / pragmatist) against the WP-spec via parallel Explore agents using the "Plan agent type, Explore subagent for DO-NOT-EDIT mandate" pattern per Reading A discipline. R-cycle to R-FIXPOINT MET. Operator-attended merge of WP-spec. | Tier 1 (plan-stage, sub-agent dispatch only) |
| Z.2 | Codex Tier 2 fire on impl per the dispatch JSON. Operator-attended fire mandatory (federation-primitive kernel-dangerous). 3-lens impl R-cycle (R1 minimum; R2 if R1 surfaces HIGH/CRIT). Cure-worse trigger discipline per `feedback_asymptotic_trajectory_split.md`. | Tier 2 (federation-primitive write) |
| Z.3 (post-merge first-fire) | Operator-attended SCP-self synthetic-opt-in fire test. Verify Inv-B + Inv-D fire visibly + Inv-C fails-closed on a SHA-mismatch fixture. Revert synthetic-opt-in once verified. | Operator-attended ceremony |
| Z.4 (post-fire close-out) | STATUS chain row flipping SCP-R-006 status from "Rego-only / vacuous-pass" → "PR-level evaluation LIVE". Update OVERVIEW.md §"What SCP enforces" rule-status table. v1.5.0 release ceremony (Z.2 is content-addition kernel-dangerous; ship a minor bump). | Operator-attended bookkeeping |

## 5. Risks

1. **Cross-mode contamination.** Sidecar invocation must not leak `pr-input.json` content into per-file evaluations of unrelated rules. Mitigation: separate conftest invocation with separate `--data` / target list; verified by Z.2 unit test exercising SCP-R-002 against `pr-input.json` and asserting no SCP-R-002 finding emitted.
2. **CT fetch failure on the federated path.** If CT-published path is missing or unreachable, the workflow must fail-CLOSED when adopter opted in (acc-cross-repo-caller-scoped: true) — silent vacuous-pass under fetch failure would be a Inv-C tamper-defence bypass. Verified by Z.2 unit test simulating gh api 404.
3. **Ed25519 verification surface.** In-job signature verification adds a Python-cryptography dependency on the runner; pinned via lockfile alongside existing conftest/opa/regal pins. Quarterly review of vendored CT public key (TF-D036-PUBKEY-ROTATION-001; carry-forward).
4. **PR-level invocation timing.** Sidecar invocation runs AFTER per-file invocation. If per-file invocation fails (e.g. infra-failure), sidecar should still attempt — OR explicitly skip with a documented signal. Decision: skip with `SCP-INFO-PR-LEVEL-SKIPPED-ON-PER-FILE-FAIL` signal in policy-findings.json so operator can disambiguate "Inv-* not fired" from "PR-level evaluation didn't run."
5. **Operator-attended fire failure.** Z.2 is kernel-dangerous (workflow extension); first-fire failure cascades to all adopters because they all call the reusable workflow. Mitigation: Z.2 implementation MUST pass the existing workflow-selftest harness before merge; Z.2 dispatch JSON's verify_commands include `bash tests/workflow/run-selftest.sh` invocations across 4 new fixture sub-cases (PR-level happy / PR-level Inv-C fires / PR-level vacuous when not opted-in / per-file rules unchanged).

## 6. Anti-scope

- NOT changing per-file evaluation semantics of any existing rule.
- NOT touching ACC-side cosignal HMAC verification (D-036 Element 5; runtime concern).
- NOT shipping the optional caching/TTL surface for cross-repo fetches.
- NOT extending the GitHub App's `Repository access` scope (sub-option α.2 deferred per §3.2).
- NOT moving CT-published artefact paths from public to App-token-gated (sub-option α.1 chosen).

## 7. Decisions reserved

- No new D-NNN reservation. This WP-spec inherits D-036 Element 1+2+3+4 ratification + RULE-003 §3.4 Implementation sketch authority.
- If §3.2 sub-option α.1 → α.2 swap becomes desirable mid-impl, file a sibling D-057 (or next available) inline with the Z.2 fire.

## 8. R-cycle protocol

- **Z.1 (WP-spec review):** 3-lens R1 plan-stage review via parallel Explore agents. Lenses: correctness / safety_bypass / completeness_governance per `feedback_orchestrator_auth_surface_plan_review_default.md` (workflow extension touches the federation primitive's input surface — auth-adjacent). R-cycle to R-FIXPOINT MET; max R3 with Option A R4 mechanical override per `feedback_asymptotic_trajectory_split.md`.
- **Z.2 (impl R-cycle):** 3-lens R1 minimum + R2 if R1 surfaces HIGH/CRIT. Cure-worse trigger discipline.
- **Operator-attended fire:** mandatory at Z.2 (federation-primitive write).

## 9. Cure-worse trigger discipline

Per Recommender Option B pre-review formalisation + `feedback_asymptotic_trajectory_split.md`: if Z.1's R1 surfaces NEW HIGH/CRIT ≥ original-R1-severity in same WP-class on R2 → invoke cure-worse rule: file SHIP-PROPOSAL + stand down + do NOT iterate R3 without explicit operator authorization. Reading A item 14 applies.

## 10. Open questions for operator-attended fire (Z.2)

1. **CT-published path canonicalisation.** Does CT already publish `governance/published/estate_repos.yaml`? If not, this WP-spec's first-fire blocks on CT-side publish slice (file as TF-D036-CT-PUBLISH-001). The §3.2 sub-option α.1 model is contingent on this path existing.
2. **CT public-key custody.** Where does the SCP-vendored `vendor/ct-cosignal-public-key.pem` come from? If CT hasn't published a stable cosignal public key yet, the Ed25519 verification surface blocks; file as TF-D036-CT-PUBKEY-001.
3. **Synthetic SCP-self opt-in fixture.** Should Z.3's fire-test use a temporary PR that flips SCP-self to `acc-cross-repo-caller-scoped: true` then reverts, OR a dedicated `tests/workflow/fixture-scp-r-006-prleveL/` harness invocation? Default to fixture-only (lower risk; matches existing workflow-selftest pattern).
4. **v1.4.0 vs v1.5.0 bump.** This is content-addition + workflow extension (NOT a breaking change to per-file rules). Bump v1.4.0 (minor) at first-fire merge; or wait for SCP-R-006-LIVE close-out (Z.4) to bump v1.5.0? Default to v1.4.0 at Z.2 merge.

---

**Status:** v0.1 DRAFT — 3-lens R1 review pending. Z.2 Codex Tier 2 fire HELD for operator-attended authorisation post-merge of THIS WP-spec PR.
