# WP-SCP-022 slice 020L — FIX-ROUND-1

**Date:** 2026-05-02
**Branch:** `feature/wp-scp-022-020l-rule-rfc-dogfood`
**Closes:** R1 review findings from `review-correctness.json` + `review-safety.json` + `review-completeness.json`.

## R1 finding inventory + closure

3-lens R1 returned **0 CRIT, 7 MAJ, 6 MIN, 4 nit** (deduped). Two MAJ duplicate across lenses (criterion-xiv over-specification surfaced by both safety and completeness). All findings closed inline in this fix-round.

### MAJ closures (7)

| Finding | Lens | Closure |
|---|---|---|
| **COR-MAJ-001** — wrong helper name `scp_has_nonempty_string` (§3.1) | correctness | Inline-fix in §3.1: `scp_r_004_has_nonempty_string` (own predicate; see SAFE-MAJ-001 closure pattern below). |
| **COR-MAJ-002** — regex HTTPS-only in §3.1 (parenthetical says HTTP+HTTPS); §10 HTTP question misclassified `[deferrable]` | correctness | Inline-fix: §3.1 regex now `https?://[^\s]+` (matches §3.4 + §6); §10 HTTP question reclassified `[BLOCKING]` (HTTP/HTTPS boundary changes match scope per RULE-TEMPLATE.md §10). Pre-resolution stands. |
| **COR-MAJ-003** — §3.4 deny-rule comment incorrectly claimed warn rules emit raw findings | correctness | Inline-fix: comment rewritten to clarify the deny rule fires on raw unwaived findings; the workflow's "Emit per-rule warning annotations" step adds SCP-R-004 to the warn-class set so deny output is treated as `::warning::`. The two warn rules emit suppression-observability records ONLY, matching SCP-R-001/002/003 pattern. |
| **SAFE-MAJ-001** — hard cross-rule dependency on `scp_r_002_*` helpers → silent-bypass risk if TF-008 refactors | safety | Inline-fix: SCP-R-004 defines its OWN `scp_r_004_is_waiver_payload` and `scp_r_004_has_nonempty_string` predicates (semantically identical to SCP-R-002's). Closes the silent-bypass hole. §10 [deferrable] resolution on common-helper promotion explicitly coordinates with this closure plan. |
| **SAFE-MAJ-002** — trivial-URL bypass not enumerated in §5 | safety | Inline-fix: §5 implicit-exclusion set adds case 5 "Residual known bypass" naming the bypass explicitly. §4 FP-3 already noted it as adversarial-only; §5 now makes the residual posture front-and-center for reviewers. |
| **COMP-MAJ-001** — §11 missing standalone `policies/VERSIONING.md` citation | completeness | Inline-fix: added to §11 "RFC infrastructure" subsection with line "policies/VERSIONING.md — semver contract governing the v1.1.0 MINOR bump target for this rule." |
| **COMP-MAJ-002** (≅ SAFE-MIN-002) — DISPATCH-NOTE criterion (xiv) over-specifies PR description for non-bypass proposals | completeness | Inline-fix: criterion (xiv) rewritten to match `README.md` §Process step 2 — non-bypass proposals require only a one-sentence Bypass-surface statement; full enumeration paragraph required only for bypass-introducing proposals. |
| **COMP-MAJ-003** — RULE-NNN ↔ RFC-NNN ↔ SCP-R-NNN naming/numbering convention undocumented in README | completeness | Inline-fix: `README.md` §Process step 1 amended with a "Naming conventions" paragraph documenting RULE-NNN.md as the file name, RFC-NNN as informal shorthand, and the decoupling from SCP-R-NNN sequence (RULE-001 → SCP-R-004 because R-001/002/003 already exist). |
| **COMP-MAJ-004** — `defer` and `scp-rule-proposal` labels not provisioned | completeness | Inline-closed: both labels created via `gh label create` (`defer` color D4C5F9 light purple; `scp-rule-proposal` color 0E8A16 green). New "Labels" section added to `README.md` between Process and Auto-defer mechanics documenting both labels. |

### MIN closures (6)

| Finding | Lens | Closure |
|---|---|---|
| **COR-MIN-001** — annotation contract richer than §3.4 sketch | correctness | Inline-fix: explicit Phase-2 enrichment note in §3.4 sprintf comment naming rule_id/finding_id object.get + 80-char truncation per §3.3. |
| **COR-MIN-002** — "array is non-empty" condition not enforced by `scp_r_004_is_waiver_payload` | correctness | Inline-fix: §3.1 second bullet revised to clarify the condition is implicit (empty array yields no `some` bindings) and the guard predicate is intentionally true for both empty and non-empty arrays. |
| **SAFE-MIN-001** — meta-waiver §5 description misleading | safety | Inline-fix: §5 third bullet rewritten — meta-waiver MUST itself contain a URL in `reason` OR operator uses rule-config disable. Meta-waiver without URL is itself a raw finding. |
| **SAFE-MIN-002** (= COMP-MAJ-002) | safety | See COMP-MAJ-002 above. |
| **COMP-MIN-001** — single-operator self-approval shape not addressed in README | completeness | Inline-fix: `README.md` §Process step 2 quorum section adds a "Single-operator self-approval shape" bullet documenting that quorum-1 in single-operator mode is satisfied by the operator's explicit merge action after the 48h window (NOT a GitHub review approval, which GitHub forbids for PR authors). |
| **COMP-MIN-002** — merge-time D-NNN ambiguity per README §3 | completeness | Inline-fix: §9 of RULE-001 adds an explicit position — SCP-R-004 is same-domain as SCP-R-002 (waivers domain), no merge-time D-NNN required per README §3. Phase-2 estate-coordination D-NNN (§7) is independent. |
| **COMP-MIN-003** (= SAFE-NIT-001) — warn rule sketch placeholders `...` | completeness | Inline-fix: §3.4 warn rule record shapes expanded to match SCP-R-001/002/003 fully: `waiver_id`, `finding_id`, `expires_at`, `file`, `msg` for waiver variant; `kind`, `rule_id`, `reason`, `expires_at`, `msg` for rule_config variant. |
| **COMP-MIN-004** — STATUS.md "Today's chain (2026-05-02)" 020L row + backlog amendment | completeness | **Deferred to merge commit / close-out** per criterion (xvii) of DISPATCH-NOTE.md. Pre-merge state is correct; STATUS.md backfill happens after the proposal merges. |

### nit closures (4)

| Finding | Lens | Closure |
|---|---|---|
| **COR-NIT-001** — Unicode-whitespace divergence between Python `re` (Unicode-aware) and OPA RE2 (ASCII-only) for `\S` | correctness | Inline-fix: §6.3 expanded with explicit Unicode-whitespace caveat naming the divergence + filed as **TF-020L-001**. Closure path: Phase-2 monitors SCP self-dogfood gate for `SCP-E005` flap on Unicode-whitespace input; if observed, anchor regex to ASCII-only printable range (`https?://[\x21-\x7e]+`) in both engines. |
| **SAFE-NIT-001** (= COMP-MIN-003) | safety | See COMP-MIN-003 above. |
| **SAFE-NIT-002** (= COR-MAJ-002) | safety | See COR-MAJ-002 above. |
| **COMP-NIT-001** — `scp_r_004_remediation_url` uses `/blob/main/` (could break on file rename) | completeness | Acknowledged as Phase-2 implementation concern; no proposal-text edit needed. The Phase-2 implementation can choose a stable permalink (commit-SHA or release page) at implementation time. Documented in this fix-round-1 as a Phase-2 hint, not in the proposal body. |
| **COMP-NIT-002** — front-matter "waivable" wording could imply window itself is skippable | completeness | Inline-fix: front-matter parenthetical now says "the standard extendable variant — the author may extend if the proposal is substantial; zero approvals at close auto-defers" instead of "waivable variant". |

## Tracked-forward filed in this fix-round

- **TF-020L-001** — Unicode-whitespace regex-engine divergence in conflict-gate (Python `\S` Unicode-aware vs OPA RE2 ASCII-only). Closure path: Phase-2 monitors SCP self-dogfood gate for `SCP-E005` flap on Unicode-whitespace input; if observed, anchor regex to ASCII-only printable range. Close as no-op if no divergence surfaces during the warn-baseline observation window. Filed at 020L R1 COR-NIT-001 closure.

## Files touched in fix-round-1

- `docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md` — front-matter wording, §3.1, §3.4, §5, §6.3, §9, §10, §11.
- `docs/reviews/WP-SCP-022/dispatches/020l/DISPATCH-NOTE.md` — criterion (xiv).
- `docs/reviews/rule-proposals/README.md` — §Process step 1 (naming conventions), §Process step 2 (single-operator self-approval), §Process step 3 (label cross-reference), new §Labels section.
- `docs/reviews/WP-SCP-022/dispatches/020l/FIX-ROUND-1.md` (this file).

## GitHub repo state changes in fix-round-1

- **Label `scp-rule-proposal` created** (color `0E8A16`, green; description "Proposal PR for new SCP-R rule, threshold change, or deprecation").
- **Label `defer` created** (color `D4C5F9`, light purple; description "Proposal auto-deferred after 48h window with zero approvals").

## Outstanding (deferred)

- **COMP-MIN-004** — STATUS.md "Today's chain (2026-05-02)" 020L row + Post-Threshold-A backlog amendment. **Deferred to merge / close-out commit per DISPATCH-NOTE criterion (xvii).** STATUS.md update happens after the proposal merges so the chain row reflects the merged-PR number + commit SHA.

## Fixpoint posture

This fix-round closes every R1 inline-actionable finding. R2 review confirms fixpoint (no new CRIT/MAJ on a complete cycle). If R2 surfaces fresh MAJ/CRIT findings, fix-round-2 follows; otherwise the proposal is at fixpoint and the slice proceeds to the operator-approval + 48h-window walk.
