# WP-SCP-026-Z — CT-side prerequisites memo (Z.2 fire dependency)

**Filed:** 2026-05-26
**WP:** WP-SCP-026 slice Z (SCP-R-006 workflow-input materialisation)
**Z.2 dispatch:** queued; **OUT OF SCOPE** of this memo (Tier 2 kernel-dangerous; operator-attended)
**Scope of this memo:** SCP-side coordination memo documenting what CT must publish before Z.2 can fire safely.
**Anti-scope:** this memo does NOT touch the CT repo or fire Z.2. It is the SCP-side handoff for CT-team action.

---

## 1. What CT must publish before Z.2 fires

Z.2 fires the SCP-R-006 workflow-input materialisation per
`docs/plans/WP-SCP-026-Z-r006-workflow-input-materialisation.md` v0.2. SCP-R-006
references three artefacts that live in CT-owned territory. Until all three are
published + machine-fetchable from SCP CI, SCP-R-006 stays inert (vacuous-pass
per Z plan-doc §"Safe failure mode"; no behaviour change on adopters).

### 1.1 `control-tower/config/estate_repos.yaml`

**Schema:** `schemas/estate-repos.schema.json` (SCP repo; already merged).

**Skeleton:**

```yaml
schema_version: "1.0.0"
services:
  - service_id: "acc"
    acc_sa_uuid: "<ACC service-account UUID — confirm with ACC team or read from ACC's identity store>"
    target_repo_app_id: null   # populated post-WS-EST-P-2 when first target is onboarded
  # Add other estate services as their App-credential surfaces are wired
  # (PIM, mapp-doc-agent, Recommender, shopify-app, FLA, RI, SA, VS).
  # Each row's service_id must match runtime_contract.allowed_callers[i]
  # per RULE-003 §3.1 Inv-A pattern.
```

**Where it lives:** `~/Projects/control-tower/control-tower/config/estate_repos.yaml`
(CT repo). Published via the CT cosignal Renovate cascade once the file lands.

### 1.2 `control-tower/governance/published/cosignal-manifest.json`

**Schema:** `schemas/cosignal-manifest.schema.json` (SCP repo; already merged).

**Skeleton:**

```json
{
  "schema_version": "d-036-mcp-manifest-v1",
  "signed_at": "2026-MM-DDTHH:MM:SSZ",
  "key_id": "ct-mcp-manifest-key-1",
  "signature": "<base64-Ed25519 over JCS-canonical-JSON of all sibling fields except `signature`>",
  "entries": []
}
```

**Notes:**

- `entries[]` is empty at first publication; CT populates per-target as each
  estate repo onboards. Inv-C resolves vacuously (no entries → no SHA mismatch
  possible) until the first entry lands.
- `signed_at` staleness: warn at >7 days, deny at >30 days per the schema's
  description (exact thresholds TBD via separate CT-owned RFC).
- Schema version evolution per D-036 Element 3: JWKS-style multi-version
  coexistence; version-allowlist enforced in the workflow consumer; additive
  changes ship as PATCH/MINOR; field removal or rename is MAJOR.

### 1.3 CT cosignal Ed25519 PUBLIC key

**Format:** PEM, ssh-ed25519 or equivalent thumbprint.

**Recommended publication path:** `control-tower/governance/published/cosignal-public-key.pem`
(stable URL — fetchable from SCP CI via `gh api repos/jrnb2024/control-tower/contents/governance/published/cosignal-public-key.pem`).

**SCP vendor path:** `vendor/ct-cosignal-public-key.pem` (SCP-side committed
copy; pinned at the published key's content-SHA). Rotation cadence + ceremony
documented separately (see §2 D-1).

## 2. Operator decision points

These decisions are operator-attended (D-031 single-operator-mode) and unblock
Z.2:

### D-1 — Manifest signing-key custody

Where does the `ct-mcp-manifest-key-1` PRIVATE key live?

- **(a) Operator's local machine.** Acknowledges D-031 bus-factor-1. Operator
  signs each manifest publication via local `ssh-keygen` (or equivalent). File
  TF-D036-010 SOP for quarterly rotation per the existing 2026-07-21 +
  2026-07-30 bus-factor-1 review cadence (per `feedback_no_silent_descoping`).
- **(b) CT repo secrets** (e.g. `CT_COSIGNAL_PRIVATE_KEY` in CT repo Actions
  secrets). Removes the local-machine dependency; introduces a CT-CI signing
  surface. Adds a new attack target (CT CI compromise → manifest forgery).
- **(c) GitHub App-credential surface** (matches D-050 pattern). Higher cost;
  matches the existing federation-primitive auth surface; operator-paced.

**Recommendation (not a decision):** start with (a) for v1 — matches D-031
single-operator-mode + has clear rotation discipline; revisit after 026F
observation if signing cadence becomes the bottleneck.

### D-2 — ACC SA UUID value

What's the value of the `services[].acc_sa_uuid` field for the `acc` row?

- Confirm with ACC team — source is ACC's identity store OR
  `.acc/credentials/` (operator-side).
- Once confirmed, ship in §1.1's skeleton in the first CT publish.

### D-3 — Sequencing relative to Z.2 fire

Two options:

- **(a) CT publishes first; Z.2 fires after.** Recommended (see §3).
  1-2 days operator-attended on CT-side; Z.2 fires on SCP-side once
  all 3 artefacts (§1.1 + §1.2 + §1.3) are machine-fetchable.
- **(b) Z.2 fires first with "pending CT publication" caveat in PR
  body, CT catches up immediately after.** Tighter operator latency
  but exposes a temporal window where SCP-R-006 fires inconsistently
  (some PRs evaluated under the inert vacuous-pass; some under
  full-rule semantics). Mitigated by SCP-R-006's safe-failure-mode
  default but creates audit-trail muddiness.

## 3. Recommended path

**CT publishes first (1-2 days operator-attended), THEN Z.2 fires on SCP-side.**

Rationale:

- Cleaner sequencing — no temporal window where SCP-R-006 fires inconsistently.
- Z.2 first-fire validates the rule on real artefacts (not on placeholder /
  vacuous-pass state).
- Matches the WP-SCP-024 cohort cascade pattern (publish + verify before flip;
  see FUP-WP-SCP-024-SMOKE-TEST-BEFORE-FLIP-001 closure in Phase 5 Bundle A
  PR #182 — same discipline applied at the rule-fire surface).
- Aligns with the broader WP-SCP-026 Shape C ratification (D-054) of
  "ship one real consumer fast + defer the multi-week build" — Z.2 is the
  consumer; CT publication is the prerequisite, not the rule.

## 4. Until Z.2 fires

SCP-R-006 stays inert (workflow inputs not materialised). Vacuous-pass on
all adopters who set `acc-cross-repo-caller-scoped: false` (the default).
Safe failure mode preserved per Z plan-doc §"Safe failure mode".

Concretely:

- Cohort adopters (PIM 2026-05-24 + CT 2026-05-25 + mapp-doc-agent 2026-05-25
  LIVE; Recommender DEFERRED; shopify-app PENDING) see no behavioural change.
- The federation primitive's `policy-check / scp/policy-check` continues to
  enforce the 6 currently-enabled rules. No regression risk.
- The Z.2 fire is the inflection point at which adopters opt into the
  `acc-cross-repo-caller-scoped: true` semantic — once Z.2 fires AND the
  per-adopter wrapper input flips, the rule activates.

## 5. Coordination with WP-SCP-026 026F observation window

Z.2 is independent of the WP-SCP-026 026F observation window (the 4-week
window from the 026C RFC merge on 2026-05-26 — see
`docs/coordination/2026-05-26-WP-SCP-026-026C-ACC-RI-canary-handoff.md`).

- 026F observes consumer adoption of `scp-cli consult` (the MCP consult surface).
- Z.2 fires the federation-primitive rule SCP-R-006 (the merge-gate surface).
- The two surfaces are additive but independent.

## 6. ACC-team action — none required from this memo

This memo is operator-attended SCP-side bookkeeping. ACC team has no action;
the ACC SA UUID confirmation in §D-2 is conversational, not a coordination
demand.

The CT-team action is concrete:

1. Author `control-tower/config/estate_repos.yaml` per §1.1 (operator-attended).
2. Author + sign `control-tower/governance/published/cosignal-manifest.json` per §1.2 (operator-attended; depends on D-1).
3. Publish CT cosignal Ed25519 public key per §1.3 (operator-attended; depends on D-1).
4. Notify SCP-side once all three artefacts are machine-fetchable (operator-paced; could be inline in a CT PR description or a notification entry under `~/Projects/control-tower/governance/docs/notifications/`).

## 7. References

- `docs/plans/WP-SCP-026-Z-r006-workflow-input-materialisation.md` v0.2 (SCP-side Z plan-doc)
- `docs/governance/work-packages/wp-scp-026-z-r006-workflow-input.json` v0.2 (Z dispatch JSON)
- `schemas/estate-repos.schema.json` (target schema for §1.1)
- `schemas/cosignal-manifest.schema.json` (target schema for §1.2)
- `docs/DECISIONS.md` D-036 (RULE-003 / SCP-R-006 reference architecture)
- `docs/decisions/D-050-app-credential-surface-2026-05-21.md` (CT-side auth surface precedent)
- `docs/coordination/2026-05-26-WP-SCP-026-026C-ACC-RI-canary-handoff.md` (sibling 026C RFC)

## 8. Out-of-scope

This memo does NOT:

- Fire Z.2 (Tier 2 kernel-dangerous; operator-attended; SCP plan-doc Phase Z covers the fire mechanics).
- Modify CT repo files (CT-team-owned changes).
- Specify the manifest signing-key rotation SOP (deferred to TF-D036-010 if D-1 option (a) selected).
- Specify the CT cosignal Renovate cascade publication mechanics (CT-team-owned).
- Reserve a D-NNN slot (this memo is coordination-only; no decision is filed).

## 9. Forward action

- **SCP-side (this memo merge):** publishes the CT-team-facing prerequisites contract; no behaviour change.
- **CT-team-side:** §6 enumerated steps 1-4.
- **No operator action required for the memo itself** — autonomous merge per Phase 6 discipline (coordination-only doc).
- **Z.2 fire:** queued; awaits CT publication confirmation per §3 recommendation.
