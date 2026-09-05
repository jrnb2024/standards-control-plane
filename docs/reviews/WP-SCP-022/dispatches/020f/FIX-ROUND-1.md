# WP-SCP-022 slice 020F — fix round 1

**Date:** 2026-04-30 (evening)
**Triggered by:** R1 review × 3 surfaced 1 CRIT + 7 MAJ + 5 MIN + 4 nit findings.

## R1 verdicts

| Lens | Verdict | Findings |
|---|---|---|
| correctness | FAIL | 2 MAJ + 1 MIN + 1 nit |
| safety_bypass | CHANGES_REQUESTED | 1 CRIT + 5 MAJ + 3 MIN + 1 nit |
| completeness_governance | NOT_ACCEPTED | 3 MAJ + 2 MIN + 2 nit |

The CRIT is real: `renovate/v*` tag series unprotected. The two MAJ correctness findings (regex won't match wrapper's non-semver tag-comment) point at the same root issue.

## Findings addressed in this fix round

### CRITICAL (CRIT-SAFE-001)

**`renovate/v*` tag series unprotected.** 020J ruleset matches `refs/tags/v*` (literal v-prefix), not `refs/tags/renovate/v*`. **Closed:** added `scripts/configure-020f-renovate-tag-protection.sh` (mirrors 020J shape) creating ruleset `scp-tag-protection-renovate-v` covering `refs/tags/renovate/v*` with same protections (deletion / non_fast_forward / update blocked).

### Correctness (COR-001 + COR-002)

**Wrapper `# tag:` comment isn't semver, regex won't match.** The actual comment was `post-v1.0.0 + warn-msg fix (020D1.1)` — Renovate's `v?[0-9]` regex + `versioningTemplate: semver` would both reject it. **Closed:** wrapper comment updated to `# tag: v1.0.0` (the SHA `41a5299` is on the v1.0.0 lineage; the comment-tag identifies the release-track for Renovate, not the exact tag-of-commit).

### Safety hardening (MAJ-SAFE-002..006)

- **MAJ-SAFE-002** (preset extends without tag pin): tracked-forward as **TF-020F-001**. Cannot be closed in this PR — `renovate/v1.0.0` is post-merge of THIS slice. Once tagged post-merge, `renovate.json` updates to `extends: ["github>jrnb2024/standards-control-plane//renovate/default#renovate/v1.0.0"]`.
- **MAJ-SAFE-003** (adopter packageRule override of automerge): **closed** by asserting `automerge: false` at multiple layers (root + scp-federation packageRule) + adding explicit description text + ADOPT-001 §12 entry (lands in 020H part 3).
- **MAJ-SAFE-004** (`ignoreUnstable: false` globally enables RC bumps for everything): **closed** — flipped to `ignoreUnstable: true` at root level. The scp-federation packageRule explicitly opts in via `ignoreUnstable: false` so adopters still receive rc.N proposals for the federation primitive.
- **MAJ-SAFE-005** (`config:recommended` is a Mend-controlled floating ref): **partially closed** — added explicit `automerge: false` at root level, so any `config:recommended` change can't silently flip it. Full closure (pinning `config:recommended` itself) is impractical — it's a Renovate-org built-in. Trust assumption documented in preset description.
- **MAJ-SAFE-006** (Dependabot wildcard group masks compromised-action bumps): **closed** — added `exclude-patterns` for the privileged actions (`actions/checkout`, `actions/upload-artifact`, `actions/download-artifact`, `actions/setup-*`). These get individual ungrouped PRs.

### Completeness (COMP-001..006)

- **COMP-001** (regex won't match wrapper): same as COR-001/002. Closed via wrapper-comment fix.
- **COMP-002** (marker convention undocumented because 020H.3 not shipped): **acknowledged-deferred**. Tracked-forward as **TF-020F-002**. Resolution: 020H part 3 ships next; the marker convention is documented inline in `renovate/default.json`'s description field as bridge documentation.
- **COMP-003** (DISPATCH-NOTE checklist (iii) ticked but tag isn't cut yet): **closed** — checklist item changed to unticked + note that it's a post-merge step. Track-forward **TF-020F-003** for the tag cut.
- **COMP-004** (plan §4 020F (i) repo-name typo `standards-control-plane` missing trailing dash): **closed** — verified via grep that this slice's artefacts use the correct trailing-dash form. The plan-text typo is a pre-existing defect; tracked separately as **TF-020F-004** (plan-text fix in a future opportunistic commit; not blocking 020F).
- **COMP-005** (renovate/v* tag protection): same as CRIT-SAFE-001. Closed.
- **COMP-006** (no evidence artefact for U-sec-3/U-gov-1 closure): **closed** — added explicit verification block to DISPATCH-NOTE.md citing the Renovate dashboard URL.

### Lower severity (closed in this round or noted)

- **MIN-SAFE-007** (vulnerabilityAlerts throttled by parent prHourlyLimit): **closed** — added `prHourlyLimit: 0` inside the vulnerabilityAlerts stanza (Renovate supports per-context overrides).
- **MIN-SAFE-008** (release-notes link is mutable): **closed** — added explicit "release notes are mutable; commit SHA is authoritative" note to prBodyNotes.
- **MIN-SAFE-009** (predictable Monday schedule): **acknowledged**. Single-operator estate; predictable schedule benefits the operator's mental model. Documented in DISPATCH-NOTE as accepted risk; revisit at the 2026-07-21 quarterly bus-factor-1 review.
- **nit-SAFE-010** (Mend trust boundary undocumented): **closed** — added trust-boundary note to preset description.
- **COR-003** (renovate.json missing tag pin): **deferred** — same as MAJ-SAFE-002 (TF-020F-001).
- **COR-004** (potential double-v in URL): **closed** — `prBodyNotes` URL now uses `{{newValue}}` alone (no leading `v`).
- **nit-COMP-007** (no STATUS.md update commitment): **closed** — added checklist item to DISPATCH-NOTE.
- **nit-COMP-008** (preset `extends:` is manual): **closed** — documented in DISPATCH-NOTE.

## Tracked-forward items added

- **TF-020F-001**: Update `renovate.json` `extends:` to pin `#renovate/v1.0.0` after the renovate/v1.0.0 tag is cut. Trivially closeable in a follow-up PR within hours of 020F merge.
- **TF-020F-002**: 020H part 3 (next slice) ships the canonical adopter wrapper marker convention. Until then, the marker is documented inline in `renovate/default.json` description.
- **TF-020F-003**: Cut `renovate/v1.0.0` tag from this slice's merge commit (post-merge).
- **TF-020F-004**: Plan §4 020F (i) text uses `standards-control-plane` without trailing dash; fix in opportunistic plan-text commit.

## Files modified

- `.github/workflows/policy-check-wrapper.yml` — `# tag:` comment → `v1.0.0`.
- `renovate/default.json` — root automerge=false, root ignoreUnstable=true, scp-federation packageRule explicit ignoreUnstable=false, prBodyNotes hardened, vulnerabilityAlerts.prHourlyLimit=0, description carries trust-boundary + adopter-override-warning.
- `.github/dependabot.yml` — wildcard group excludes privileged actions.
- `scripts/configure-020f-renovate-tag-protection.sh` — new (idempotent applier for renovate/v* protection).
- `docs/reviews/WP-SCP-022/dispatches/020f/DISPATCH-NOTE.md` — checklist accuracy + verification artefact + tracked-forward items.
- `docs/reviews/WP-SCP-022/dispatches/020f/FIX-ROUND-1.md` — this file.

## Next step

R2 dispatch on the corrected artefact set. Per `feedback_recursive_adversarial_review.md`, recurse to fixpoint.
