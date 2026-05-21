# TF-PIM-001 impl WP — pragmatist lens R1 review (v0.2)

**Dispatched:** 2026-05-21 PM against impl WP plan-doc v0.2 at `ef5312e`
**Agent type:** Plan (read-only; DO-NOT-EDIT mandate)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens precedent:** reuse pattern from `docs/reviews/TF-PIM-001/shortlist-A-C-D/pragmatist-lens-r1.md`

---

## Lens: pragmatist — TF-PIM-001 impl WP v0.2 R1 review

### Verdict
ACCEPT-WITH-AMENDMENT

### Summary

The v0.2 impl WP is structurally sound and operationalises Path C faithfully across 8 waves. The 10 strategic-review refinements folded at v0.2 — specifically the 4-step `.pem` discipline in Wave A, the operator-attended merge clarification for Wave B, the `actions/create-github-app-token` PRIMARY / `tibdex/github-app-token` FALLBACK decision rule, the Wave D/E parallelism clarification, and the Wave F/G rollback decision tree (§7.5a + §7.6) — all represent genuine pragmatist-domain value: they reduce ceremony ambiguity, reduce operator-attention re-entrancy cost, and bound the blast radius of failure modes concretely.

PIM's `policy-check / scp/policy-check` required-check has been relaxed since 2026-05-19 (P0 open). Under v0.2 wave sequencing, Wave H restores the required-check; earliest realistic Wave H completion is day 6-7 of the 1-2 week estimate — putting the total degradation window at roughly 9-14 calendar days from ratification (2026-05-21). That is within the "time-limited + operator-attended + recoverable" framing operator accepted at convergence. The degraded state is operationally tolerable because PIM continues productive Phase 4 labeller work during the window and because D-049 explicitly decouples v1.3.0 ship from TF-PIM-001 closure. The principal pragmatist concern is not whether the plan is executable but whether two structural gaps — the SCAFFOLDER FUP unblock signal and the four non-PIM cohort adopters' onboarding path — are captured with enough specificity to be actionable after this WP closes.

### Timeline realism — wave-by-wave

| Wave | Realistic estimate | Cumulative |
|---|---|---|
| A — App authoring (UI + 4-step .pem discipline) | 30-45 min | Day 0 |
| B — D-050 ADR drafting + operator-attended merge | 2-4 hours + operator availability | Day 1 |
| C — ADOPT-001 §12.7 updates | 2-3 hours | Day 1-2 |
| D — Reusable workflow change (Tier 2 Codex + R-cycle to R-fixpoint) | **2-4 days (calendar driver)** | Day 3-5 |
| E — Selftest fixture (parallel with D authoring; verify gated on D landing) | 1-2 hours parallel | Day 3-5 |
| F — SCP-self dogfood verify | 15-20 min | Day 5 |
| G — PIM canary App install + cross-repo verify | 30-45 min | Day 5-6 |
| H — PIM required-check restoration + closure | 15-20 min | Day 6-7 |

**Cumulative realistic estimate:** 6-9 calendar days nominal. Upper-tail (Wave D R3 cure-worse + Option A R4 mechanical override): 10-14 calendar days. The "1-2 week" estimate from parent plan-doc §5 is defensible but NOT robust to a single Wave D cure-worse event. If Wave D R3 introduces a regression, the R4 mechanical override adds ~2 calendar days, pushing closure to day 14-16 — past the "2-week" envelope.

### PIM degraded-state persistence under v0.2 sequencing

Restoration at Wave H. Realistic timeline 6-9 days from 2026-05-21 ratification → restoration **by 2026-05-27 to 2026-05-30** nominal. Wave D cure-worse: by 2026-06-01 to 2026-06-04. Wave F dogfood failure compounds further: 17-20 calendar days total. All within "time-limited + recoverable" framing operator accepted at convergence; no MAJ finding. But note: at outer-tail (17-20 days) the degradation window approaches operator-comfort limits if PIM Phase 4 PR volume is high.

### Findings

**PRAG-MIN-001 — SCAFFOLDER FUP unblock signal lacks close condition**

The BACKLOG row for FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001 (P1) states "Blocks until TF-PIM-001 resolution." Wave H Actions item 6 mentions "FUP unblock signal" + §9 lists the FUP. But neither §9 nor Wave H provides a close condition: what constitutes "TF-PIM-001 closure triggers FUP unblock" in machine-checkable terms? The BACKLOG row says "scaffolder can be verified against a real adopter run" — that's Wave G's PIM canary. Without explicit "Wave G success = SCAFFOLDER FUP unblocked; immediate fix path (a) from BACKLOG row; separate impl slice opens" statement in §9, the unblock may be treated as implicit, deferring the P1 scaffolder fix unnecessarily.

**Remediation:** §9 amend with explicit close condition.

**PRAG-MIN-002 — 4 non-PIM cohort adopters' App-install path lacks forward-pointer to where ceremonies are captured**

§3.2 correctly scopes PIM as in-scope; §9 says "future cascade slices (024D-024G) inherit App-install ceremony per adopter — captured in WP-SCP-024 §5.2 update at first 024D dispatch." Two gaps:
1. WP-SCP-024 §5.2 amendment at 024D dispatch is implicit; should be explicit §9 item
2. D-049 D3 commits Recommender as first deny-gate; Recommender's cascade slice is first test of §12.7.16 install ceremony in real non-PIM adopter context; flag missing from §9

**Remediation:** §9 amend (a) explicit WP-SCP-024 §5.2 amendment at 024D dispatch + (b) flag Recommender's cascade slice as first practical test of same-namespace App-install.

**PRAG-NIT-001 — Operator-attended gate batching not explicitly recommended**

Waves A (ceremony), B (merge), F (verify), G (PIM canary + App install), H (restoration + closure) are all operator-attended. Waves G+H are both short (45 min + 20 min) and logically sequential — should be batched. Similarly Waves A+B (if ADR pre-staged). Plan could add "Recommended batching" note: Waves A+B in one session; Waves G+H in one session. This reduces 5 operator-attended sessions to 3 (A+B / D-fire / G+H + mechanical F verify). Pragmatist ergonomics, not structural.

### Cohort-of-5 onboarding implications

- **PIM** — Wave G canary; §12.7.16 documents ceremony; @jrnb2024 self-install; fully captured
- **CT** — 024D cascade slice; §9 references "future cascade slices inherit App-install ceremony per adopter"; needs WP-SCP-024 §5.2 amend per PRAG-MIN-002
- **MDA** — minimal frontend; paired with Recommender; same §9 reference
- **Recommender** — D-049 D3 first deny-gate; cascade slice 024D-024G timing; PRAG-MIN-002 first-test flag missing
- **shopify-app** — SA-011 closed 2026-05-20; future deny-gate #3 per D-049; same §9 reference

**Overall cohort assessment:** PIM fully captured (Wave G). 4 remaining adopters adequately referenced via §9 but the WP-SCP-024 §5.2 amendment gap (PRAG-MIN-002) means the 024D dispatch runner must remember to look at §12.7.16. The App-install ceremony documentation in §12.7.16 is sufficient to replicate cleanly per adopter in @jrnb2024 namespace.

### D-049 §Sequencing impact

D-049 §Sequencing items 1-3 supported by v0.2 wave structure:
- Item 1 (v1.3.0 self-dogfood-only): independent of TF-PIM-001; no conflict
- Item 2 (TF-PIM-001 closes → first external adopter green): Wave G's AC #1 (PIM canary); satisfied at Wave G, not at Wave H
- Item 3 (first DPBM-scoped adopter declares = Recommender): becomes available 5-6 days after Wave A start nominal

§10 Closure ceremony correctly cross-references D-049 item 2 as artefact-gate. No finding.

### Carry-forward to R2

PRAG-MIN-001 and PRAG-MIN-002 are document-only amendments — fold into v0.3 amend before R2. PRAG-NIT-001 small spec-text addition. Neither rises to REVISE; both ACCEPT-WITH-AMENDMENT territory.

No carry-forward items from TF-PIM-001-PRAG-001 through 004 apply (those were Path-A-specific; all closed as NOT-APPLICABLE-UNDER-RATIFIED-PATH at convergence). PRAG-001 (repo-public ADR) subsumed by Wave B D-050; PRAG-002 (PIM restoration) = Wave H; PRAG-003 (SCAFFOLDER FUP unblock) partially captured but needs close-condition amendment (PRAG-MIN-001); PRAG-004 (issue tracker triage) N/A under Path C.

### Convergence signal
ITERATE-EXPECTED — 2 PRAG-MIN + 1 NIT fold into v0.3 prose; R2 expected to reach fixpoint if §9 amendments land.
