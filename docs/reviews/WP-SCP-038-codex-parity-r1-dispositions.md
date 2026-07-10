# WP-SCP-038 — plan-stage 3-lens R1 dispositions

**Date:** 2026-07-10 · **Stage:** plan (pre-build) · **Verdict:** ACCEPT with substantial folds — the
review corrected a **factual error** (Codex DOES have a hooks feature) that reshaped D3 into a stronger
design, and enforced the two-PR dormant→fire discipline. All folded into spec v2. **Reviewers:** 3×
Sonnet — correctness / safety_bypass / completeness_governance, each vs. the real SCP-R-030 template,
`codex_dispatch.py`, and `~/.codex/config.toml` (facts re-verified by the orchestrator directly).

## Correctness lens
- **C-BLOCKER-1 (FOLDED — factual correction):** v1 claimed "Codex has no hook / not possible." FALSE —
  `codex features list` → `hooks stable true`; `.codex/hooks.json` `PreToolUse` blocks on deny/exit-2
  (shell-matched). → v2 corrects the claim and **redesigns D3** around a real Codex PreToolUse hook
  (investigation-gated: does it reach the write surface?), SCP-gateable on `.codex/hooks.json` presence.
- **C-BLOCKER-2 (FOLDED):** v1's D3 keyed off `ACC_CODEX_DISPATCH_ACTIVE` "exported by the dispatcher" —
  it does NOT exist (`codex_dispatch.py:568` *removes* `ACC_PHASE_X_DISPATCH_TOKEN`, exports nothing). →
  v2 drops the invented mechanism; the fallback wrapper requires the dispatcher to write a per-invocation
  PID-bound nonce (verifiable against the dispatch log) or the logging claim is downgraded.
- **C-MAJOR-3 (FOLDED):** `schemas/rule-config.schema.json` is `additionalProperties:false` (verified) →
  the new `codex-dispatch-onboarding` opt-in key needs a schema diff. Added to D2 Phase 2.
- **C-MINOR-4 (CONFIRMED settled):** distinct opt-in key (not reuse `acc-hook-installed`) is correct — a
  repo can be a Codex target without the acc-hook.
- **C-MINOR-5 (FOLDED):** distinguish `plugin_hooks` (removed) from the stable general `hooks` — noted.
- CONFIRMED-CORRECT: SCP-R-014 is next-free; SCP-R-030 opt-in key/default/marker facts accurate;
  materialiser extension genuinely feasible in the SAME step; WARN_BASELINE both sites; D-060 real.

## Safety / bypass lens (charge: honest defense-in-depth vs theatre)
- **S-BLOCKER-1 (FOLDED):** closure-framing is the real exposure — a future "Codex parity CLOSED" TL;DR
  calcifies into false assurance. → v2 adds a verbatim honest-framing banner as a HARD acceptance criterion
  for every status/closure doc.
- **S-MAJOR-2 (FOLDED):** v1's D3 bypass description was wrong ("unset the var" isn't a bypass; the real
  one is `export …=1`) + the logging claim was unfounded (spoofed==real). → corrected in v2's D3 fallback
  + the nonce requirement.
- **S-MAJOR-3 (FOLDED):** presence≠compliance was an open question → promoted to a HARD acceptance criterion
  on SCP-R-014's finding/remediation text.
- **S-MAJOR-4 (FOLDED):** SCP-R-014 verifies the committed repo-tree AGENTS.md, not the runtime file
  (`~/.codex/AGENTS.md` global empty; `-c`/per-project overrides) → stated as an explicit D1 residual +
  the ACC handoff must sync the runtime file.
- **S-MINOR-5/6 (FOLDED):** vacuous-pass rollout window named; AGENTS.md↔dispatcher staleness noted (marker
  `v1` covers content revisions, not silent dispatcher drift).
- CONFIRMED: v1's context + D1/D3 self-deprecation were honest; no existing control weakened; D-058 split correct.

## Completeness / governance lens
- **CG-BLOCKER-1 (FOLDED):** VERSIONING.md + version-manifest.json + STATUS.md dropped from the build
  footprint (the SAME omission ARCH-006 v1 made) → added to D2 Phase 2.
- **CG-BLOCKER-2 (FOLDED):** v1 collapsed ship-dormant + fire-live into one step → v2 splits D2 into
  Phase 1 (dormant rule) + Phase 2 (companion materialiser), per every precedent (bounds blast radius on
  the kernel-dangerous `policy-check.yml`).
- **CG-MAJOR-3 (FOLDED):** propose→adjudicate compressed → v2 enumerates the four adjudicate-proposal.md
  artefacts by name (prose / index+version-bump / DECISIONS / retire PROP).
- **CG-MAJOR-4 (FOLDED):** repo scope was name-guessed + self-contradictory (SCP listed but "never uses
  Codex") → v2 SURVEYS actual `codex_dispatch` usage (acc/pim/CT/pac/SA/Recommender are the users;
  SCP/doc-agent/FOS/kg/graph-twin have zero), excludes SCP, flags the stale CLAUDE.md cohort line.
- **CG-MAJOR-5 (FOLDED):** domain choice is not symmetric — a new `agent-lifecycle` domain = closed-enum
  schema change + new dir + domain-map wiring; "governance" recommended partly on that cost.
- **CG-MAJOR-6 (FOLDED):** the ACC handoff must be a real droppable file, not spec-internal prose →
  authored at `docs/coordination/2026-07-10-WP-SCP-038-ACC-codex-parity-handoff.md`.
- **CG-MINOR-7/8/9 (FOLDED):** both deferrals filed as BACKLOG FUP rows; WP-level D-NNN flagged as a
  decision; pilot-success criteria stated.
- CONFIRMED-COMPLETE: ownership split, warn-baseline-first, propose()-needed-here (vs REACH-2), pilot-first.

## Net
Two correctness BLOCKERs (one a factual error I owned + re-verified) reshaped D3 from a bypassable shim
into a potential real Codex-side hook; the completeness lens enforced the two-PR discipline + full
footprint + a surveyed scope; the safety lens hard-wired the anti-false-assurance framing. The WP is now
honest about exactly what it does and doesn't enforce. Build remains dispatch-gated + ACC-coordinated;
the D3 PreToolUse-reaches-write-surface investigation is a required pre-build step.
