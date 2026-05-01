# RULE-NNN — <one-line title>

**Status:** DRAFT (replace with one of: DRAFT / UNDER REVIEW / ACCEPTED / DEFERRED / SUPERSEDED).
**Author:** @<github-handle>
**Filed:** YYYY-MM-DD
**Target release:** v<X>.<Y>.<Z> (SCP federation primitive).
**Type:** rule-add | rule-promote-warn-to-deny | rule-breaking-change | rule-deprecate
**Quorum required:** 1 (single-operator mode per D-031) | 2-of-N (post-second-maintainer)
**Review window:** 48h wall-clock from PR open.

---

## 1. Summary

One-paragraph description of what this proposal does and why. The
adopter who reads only this paragraph should be able to decide
whether they want to engage with the rest of the proposal.

## 2. Motivation

Why does this rule exist? Cite:

- A real-world finding (issue, incident, or manifest pattern) that
  motivated the proposal. If you cannot cite a concrete finding, this
  is probably the wrong slice — consider whether to defer.
- The threat model or governance concern this rule closes.
- Any prior conversation in `docs/reviews/` or `docs/notifications/`
  that the proposal extends.

## 3. Rule specification

### 3.1 Match conditions

What manifest shapes does this rule fire on? Be specific. Example:

> Fires when `services.yml` contains a top-level `service:` entry with
> `auth.mode: bearer_legacy` AND `expires_at` is missing or `< now`.

### 3.2 Severity & threshold

- Initial threshold: `warn` | `deny` (per `policies/VERSIONING.md`,
  new rules land at `warn` baseline; promotion to `deny` default is a
  separate proposal type).
- Adopter override: confirm `.scp/rule-config.yaml` `disable: true`
  with `justification: <string>` AND `expires_at: <date>` continues
  to suppress (all three fields are required by `schemas/rule-config.schema.json`).

### 3.3 Annotation contract

- **Error code** (annotation `title=`): `SCP-EXXX` (where XXX = a new
  code or a reuse — see ADOPT-001 §12.7.7 for the active set).
  Examples: `SCP-E003` for a deny, `SCP-E006` for a disabled-rule
  observability record.
- **Rule ID** (in annotation `message`): `SCP-R-NNN`. The rule ID
  appears in the human-readable message (e.g. `SCP-R-002:
  waivers.json schema violation`), separate from the error-code
  `title` field.
- Sibling commit-status text: must fit the
  `scp/policy-check-readback` line-length budget (~80 chars).

### 3.4 Implementation sketch

Show the Rego pattern (PoC level — implementation lands separately).
Indicate which helpers from `policies/scp_common.rego` will be reused
or extended.

## 4. False-positive surface

Every rule has one. Name the cases where this rule will fire on
legitimate manifests:

- Manifest type X (where the rule's condition is structurally true
  but the intent is fine).
- Edge case Y (path-scoping limitation, etc.).

For each, say: (a) the rate you expect (estimated FP per 100 PRs),
(b) the recommended adopter response (waive, disable via
rule-config, fix the manifest).

## 5. Bypass surface

Does this rule add a new bypass surface beyond the existing
`scp_bypass: true` + three-gate model and `.scp/rule-config.yaml`?

- New `.scp/rule-config.yaml` key? Name it.
- New `scp_bypass: <variant>` flag? Name it.
- New per-finding waiver shape? Name it.
- **Implicit exclusion set:** under what manifest shapes does this
  rule return `allow` (pass)? Enumerate the key conditions that
  make a manifest exempt. If exemption = absence of a field the
  rule requires, state that explicitly. Reviewers MUST verify the
  exemption set is intentional and does not create an unreviewed
  bypass-by-omission. Closes 020H.1 R1 SAFE-MAJ-002.

If the rule does NOT add a bypass surface, write "None — uses
existing scp_bypass three-gate + rule-config disable mechanisms."

**If §5 is non-empty,** the proposal triggers the non-waivable 48h
window per `README.md` "Bypass-introducing proposals" — the PR
description MUST include an explicit "Bypass surface enumeration"
paragraph naming every adopter-side control governing the surface.

## 6. Conflict-gate strategy

How will this rule's Rego implementation be cross-checked against
the Python evaluator?

- Are the rule's match conditions expressible in the Python
  evaluator today? If not, what's the closure path?
- What conflict-gate fixtures will be added to `tests/conflict_gate/<rule-id>/{allow,deny}/`? Every shared fixture must pass through the existing `tests/conflict_gate/adapter.py` adapter contract.
- A conflict-gate disagreement at runtime emits `SCP-E005` and merge-blocks (per ADOPT-001 §12.7.7). The proposer should confirm the rule's fixtures will not cause the conflict-gate job to flap on the SCP self-dogfood gate before merge.

## 7. Estate-cascade considerations

- Which estate adopters (FLA, PIM, recommender, shopify-app,
  mapp-doc-agent, control-tower) are likely to opt into this rule
  immediately at `warn`?
- Which are likely to need a transition period?
- Is there an estate-wide D-NNN forward-looking decision that should
  be filed in coordination with this proposal?

## 8. Test plan

- Conftest test fixtures (`policies/tests/<rule-id>_test.rego`).
- Conflict-gate fixtures (`tests/conflict_gate/<rule-id>/{allow,deny}/`).
- Workflow-selftest harness coverage (`tests/workflow/<harness>/`).
- Canary update if the rule deny path materially changes adopter PR
  behaviour (`canary/...` branches).

## 9. Migration / rollout

Map onto `policies/VERSIONING.md` semver categories:

- New rule at `warn` → MINOR bump in v<X>.<Y+1>.0.
- Promotion to `deny` default → MAJOR bump after one MINOR's worth of
  warning annotations.

Name the target release explicitly. Adopter-side migration steps (if
any beyond the standard SHA-pin bump) go here.

## 10. Open questions

List anything the proposal leaves unresolved. Reviewers can answer
these in the PR conversation; the merged proposal incorporates the
resolution.

**Mark each question as one of:**

- **`[BLOCKING]`** — must be resolved before merge. Use this for
  any question whose answer changes the rule's match scope, severity,
  bypass surface (§5), or conflict-gate strategy (§6). A reviewer
  approving the proposal confirms every `[BLOCKING]` question is
  resolved.
- **`[deferrable]`** — implementation detail, fixture corner case,
  or future-compat consideration that does not change the rule's
  acceptance shape. Can be merged as an open question and resolved
  in the implementation PR.

A proposal with unresolved `[BLOCKING]` questions does NOT meet
quorum, even with one CODEOWNER approval. Closes 020H.1 R1
SAFE-nit-008.

## 11. References

- Cited findings (issue numbers, incident reports).
- Related rules (`SCP-R-NNN`).
- Related decisions (`docs/DECISIONS.md` D-NNN).
- ADOPT-001 §M.N if the rule changes adopter-facing onboarding text.
