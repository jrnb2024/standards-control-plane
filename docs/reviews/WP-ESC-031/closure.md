# WP-ESC-012b review closure — SCP-R-031 estate-context bootstrap-marker linkage rule

**Programme:** PLAN-CT-ESTATE-CONTEXT-001 · Phase 0-D · **Repository:** standards-control-plane
**R1 reviewed head:** `825cb1d` (base `a7393ae`) · **Fix head:** `ec57df0` · **R2:** verified (comment/test/doc only)

## What this delivers

A new **advisory (WARN-baseline)** Rego rule **SCP-R-031** that gates presence of the CT-ratified marker
`<!-- canonical:estate-context-bootstrap v1 -->` in BOTH `CLAUDE.md` and `AGENTS.md` — the load-bearing
second-file teeth over SCP-R-030 (which checks CLAUDE.md only). LINKAGE-not-VALUES (D-058): control-tower owns the
marker contract (WP-ESC-012a); SCP gates linkage only and never becomes the context authority. Opt-in via committed
`.scp/rule-config.yaml estate-context-marker: true`; vacuous-passes when inputs absent (SCP-R-006/030 safe-failure
precedent). Ships dormant-and-warn-only in production; deny-promotion + input materialisation are deferred to a
named companion PR (mirrors SCP-R-030's own split).

## Round 1 — three independent adversarial lenses (2026-07-25)

| Lens | Verdict | Findings |
|---|---|---|
| correctness | APPROVED_WITH_FINDINGS | COR-R1-001 MINOR (AGENTS.md non-string total-function clause untested); COR-R1-002 INFO (substring token match). 14/14 opa tests, 99.22% coverage; both-file logic + off-by-one + message/remediation parity all verified against SCP-R-030. |
| safety_bypass | APPROVED_WITH_FINDINGS | Advisory containment HOLDS (only in WARN_BASELINE at 2 sites; absent from REPO_LEVEL/deny/conflict-gate; cannot block a PR or emit a false deny). Vacuous-pass SAFE. Suppression no-bypass. SB-R1-001 (bounded/advisory: denylist misses structured leaks + false-positives on prose — same as 12a); SB-R1-002 (low: anti-spoof comment overclaim); SB-R1-003 (info: opt-in key absent from schema pre-companion-PR = fail-CLOSED, self-scoped). |
| completeness_governance | APPROVED (no findings) | Scope-clean (SCP-R-030 + all other rules byte-identical); companion-PR deferral explicitly documented (§5.2, not silent descope); 5 fixtures match SCP-R-030 schema; version-manifest MINOR bump correct; advisory-contained. |

## Fix round + R2 — findings dispositioned (none descoped)

| Finding | Class | Disposition |
|---|---|---|
| COR-R1-001 | MINOR | FIXED — `test_scp_r_031_agents_non_string_content_totals_empty` added; coverage 99.22% → **100%** (line 114 now load-bearing). |
| SB-R1-002 | LOW | FIXED — anti-spoof comment corrected (3 occurrences): the anchor rejects a below-window marker only; an in-window code-fenced marker is a harmless present-spoof (marker carries no authority). Comment-only. |
| SB-R1-001 / COR-R1-002 / SB-R1-003 (denylist) | bounded/advisory | NAMED companion-PR obligation (plan §5.2 item 4): before any deny-promotion, the input-materialising companion PR MUST materialise CT `marker.json`'s `dynamic_state_detectors` (shape regexes) into the eval `input` and consume them instead of the interim substring denylist — preserving CT's single source of truth (**no Rego-side regex duplication** — that would be the D-058 anti-pattern). The interim substring check is a bounded advisory heuristic; the authoritative classifier is CT's WP-ESC-012a verifier + human review + WP-ESC-012c adapter-never-writes. Deny-promotion is parked for the operator. |
| SB-R1-003 (schema coupling) | INFO | ACCEPTED — fail-CLOSED, self-scoped, intentional B.1/B.2 ordering (documented). |

**R2 (integrator, comment/test/doc-only round):** opa test **15/15**; `opa fmt --diff` clean; the SCP-R-031.rego rule
diff is **comment-only (zero logic change)**; `scripts/scp-pre-push-verify.sh` all 3 gates pass; scope-clean
(SCP-R-030, scp_common, policy-check.yml, version-manifest, schemas, fixtures untouched).

## Authority boundary

Advisory linkage gate; SCP never becomes the marker/context authority (D-058). No deny-promotion in Phase 0 — the
rule is WARN-baseline only. Rollback = deregister from WARN_BASELINE + remove policy/test/fixtures. Estate-wide
adoption + deny-promotion are PARKED for an operator gate.

## Exit state

Zero unresolved CRITICAL/HIGH/MEDIUM. Advisory-contained, vacuous-safe, single-source-of-truth preserved.
Review-converged.
