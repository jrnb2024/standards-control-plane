# RULE-001 — waiver `reason` must cite an issue/PR/decision URL

**Status:** UNDER REVIEW
**Author:** @jrnb2024
**Filed:** 2026-05-02
**Target release:** v1.1.0 (SCP federation primitive).
**Type:** rule-add
**Quorum required:** 1 (single-operator mode per D-031)
**Review window:** 48h wall-clock from PR open.
**Bypass-surface non-empty:** `false` *(§5 below adds no new `.scp/rule-config.yaml` key, no new `scp_bypass: <variant>` flag, no new per-finding waiver shape, and no non-default implicit-exclusion set. The 48h window is therefore the standard extendable variant per `README.md` — the author may extend if the proposal is substantial; zero approvals at close auto-defers. Closes WP-SCP-022 020H.1 R2 SAFE-MIN-001 — this field is machine-readable so a future tooling-level check can act on it without re-parsing the proposal text.)*

---

## 1. Summary

Add **SCP-R-004** at `threshold: warn` baseline in v1.1.0. The rule fires on each waiver entry in a waivers payload (top-level JSON array of waiver objects, per `schemas/waivers-file.schema.json`) whose `reason` field is a non-empty string but does NOT contain at least one `https://` URL. Adopters opt out via `.scp/rule-config.yaml` `disable: true` with a justification + `expires_at`, identical to every other SCP-R-NNN rule.

The motivation is auditability: SCP-R-002 enforces waiver *shape* (every entry has `reason`, `approved_by`, `created_at`, `expires_at`), and `schemas/waiver.schema.json` requires `reason` with `minLength: 1`. Today, both layers accept `reason: "approved by Jim"` — there is no machine-checkable link from the waiver to a reviewable decision artifact (issue, PR, or written decision). SCP-R-004 closes that gap by requiring at least one URL in the reason string.

## 2. Motivation

### Real-world finding

Inspect any current waiver payload (e.g. `output/findings/waivers.json` if present in a PR-time finding-store run, or any of the testdata fixtures under `policies/testdata/`) — the `reason` field is free-text. The schema and SCP-R-002 enforce that `reason` is present and non-empty, but a human reviewer must manually correlate the waiver to a decision artifact. For a single-operator estate this is tractable; for the post-WP-SCP-024 estate cascade (FLA → PIM → recommender → shopify-app → mapp-doc-agent → control-tower) the manual-correlation cost is multiplied across every adopter, and the SCP source repo cannot enforce traceability without a rule.

### Threat model / governance concern

Three concrete failure modes the absence of SCP-R-004 enables:

1. **Waiver-without-decision** — a reviewer adds `reason: "approved verbally"` and merges. The waiver passes SCP-R-002. Six months later, when the waiver expires, no operator can determine WHO approved it or under WHAT conditions. The estate has lost the ability to evaluate whether the same decision should be re-approved or whether the underlying violation should now be remediated.
2. **Waiver-without-trail** — a reviewer adds `reason: "see Slack discussion"`. Slack messages roll out of retention (typically 90 days for free-tier or unspecified-policy workspaces); the waiver outlives the trail. The waiver is effectively undocumented.
3. **Waiver-laundering** — a reviewer copies a previous waiver's `reason` field forward without re-evaluating. There is no machine-checkable indication that the new waiver represents a new decision rather than a copy-paste artifact.

A URL-bearing `reason` ties every waiver to a durable, reviewable, accountable decision artifact. Issue trackers, PR descriptions, decision log entries (e.g. `docs/DECISIONS.md` D-NNN, `docs/notifications/`) all serve.

### Prior conversation

- `README.md` §"Authorship guidance" (in this directory) explicitly directs proposals to "cite a real-world finding that motivated the rule" — this proposal cites the audit-trail gap above and the post-WP-SCP-024 multiplication problem.
- `STATUS.md` Post-Threshold-A backlog "WP-SCP-022 proposal-queue" item names this slice as the dogfood candidate.
- `CONTINUATION-PROMPT-2026-05-02-pm.md` §"What's left (next-session candidate pool) — Substantive" enumerates this rule as the recommended Phase-1 deliverable.

## 3. Rule specification

### 3.1 Match conditions

Fires when ALL of the following hold:

- The Conftest-evaluated input is a JSON array (`is_array(input) == true`) — i.e. the file under evaluation is a waivers payload per `schemas/waivers-file.schema.json`.
- The array is non-empty (implicit: an empty array yields no `some index, entry in input` bindings, so the rule body cannot succeed regardless of any guard predicate; the `scp_r_004_is_waiver_payload` guard in §3.4 returns true for both empty and non-empty arrays, mirroring SCP-R-002's intentional posture so SCP-R-002's per-entry checks can run).
- For some entry `e` in the array:
  - `e` is an object (`is_object(e) == true`).
  - `e.reason` is a non-empty string (`scp_r_004_has_nonempty_string(e, "reason") == true`).
  - `e.reason` does NOT contain a substring matching the URL pattern `https?://[^\s]+` (HTTP-or-HTTPS scheme, followed by at least one non-whitespace character; see §10 [BLOCKING] resolution on HTTP acceptance).

> **Path-scope caveat (mirrors SCP-R-002).** Conftest invokes every Rego rule against every file in the changed-file manifest. SCP-R-004's `is_array(input)` guard ensures the rule no-ops on non-array-rooted files (services.yml, expected-annotations.json, etc.). This is the same posture SCP-R-002 takes. The forward-fix (TF-008) of path-scoping the entire SCP-R-NNN rule family to specific basenames remains v1.1+ work and would benefit SCP-R-004 in the same proportion as SCP-R-002.

> **Coexistence with SCP-R-002.** SCP-R-002 raw findings include a "waiver entry N must include reason" check on every required key (verify by reading `policies/SCP-R-002.rego` `scp_r_002_required_keys` — the set includes `reason`). If `reason` is absent or empty, SCP-R-002 emits a deny on the missing field; SCP-R-004 does NOT fire (its second match condition `scp_r_004_has_nonempty_string(e, "reason")` is false). The two rules are non-overlapping by construction.

> **Self-contained Rego helpers (closes 020L R1 SAFE-MAJ-001).** SCP-R-004 defines its OWN `scp_r_004_is_waiver_payload` and `scp_r_004_has_nonempty_string` predicates (identical in semantics to SCP-R-002's predicates) rather than calling `scp_r_002_*` directly. This prevents a silent-bypass regression: if SCP-R-002 is refactored (e.g. as part of TF-008 path-scoping work), SCP-R-004's raw-findings rule continues to compile and evaluate correctly. If a future PR lifts these predicates to `policies/scp_common.rego` as cross-rule shared helpers, SCP-R-004 can switch to the common-helper version in the same PR (see §10 [deferrable] resolution on common-helper promotion).

### 3.2 Severity & threshold

- **Initial threshold:** `warn` (per `policies/VERSIONING.md` baseline for new rules).
- **Adopter override:** `.scp/rule-config.yaml` `disable: true` with `justification: <string>` AND `expires_at: <date>` continues to suppress, identical to SCP-R-001 / SCP-R-002 / SCP-R-003 (all three fields required by `schemas/rule-config.schema.json`). Adopters who need a transition period (existing waivers without URLs) can disable for one ramp window and amend waivers as they're touched.
- **Promotion to deny default:** deferred. The promotion is a separate proposal type per `README.md` §"When to file a rule proposal" and follows `policies/VERSIONING.md` "promotion to deny default lands in the MAJOR after the deprecation ramp's notice window". Earliest plausible promotion: v2.0.0, after one MINOR's worth of warn-baseline observation in adopter PRs.

### 3.3 Annotation contract

- **Infrastructure error code (annotation `title=`):** SCP-R-004 fires at warn baseline → emits `::warning file=<waivers-path>,title=SCP-R-004::<message>`. No deny → no SCP-EXXX infrastructure code involvement at PR time. (When promoted to deny in a future MAJOR, the deny path uses existing `SCP-E003` per ADOPT-001 §12.7.7 — the `SCP-EXXX` codespace remains closed; the rule does NOT claim its own SCP-E code.)
- **Rule-specific annotation message format:** `SCP-R-004 waiver entry N (rule_id=<rid>, finding_id=<fid>): reason field must contain a decision-artifact URL (issue, PR, or decision log entry). Found reason text: "<truncated-reason>"`. The truncation truncates after 80 characters with a trailing `…` if the original exceeds the budget; this keeps the annotation message reasonable while still aiding human triage.
- **Sibling commit-status text:** the `scp/policy-check-readback` line-length budget (~80 chars) is consumed primarily by the per-rule warn count line `SCP-R-004 warn: N waiver(s) missing decision URL`. Validated against the existing readback shape for SCP-R-001 / SCP-R-002 / SCP-R-003.
- **Disabled-rule observability (rule-config disable path):** unchanged from existing infrastructure — `SCP-E006` informational annotation per ADOPT-001 §12.7.7.

### 3.4 Implementation sketch

```rego
package main

import rego.v1

scp_r_004_rule_id := "SCP-R-004"

scp_r_004_remediation_url := concat("", [
  "https://github.com/jrnb2024/standards-control-plane-/blob/main/",
  "docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md",
])

# Self-contained guard predicates — semantically identical to SCP-R-002's
# `scp_r_002_is_waiver_payload` and `scp_r_002_has_nonempty_string`, but
# named into the SCP-R-004 namespace so a TF-008 refactor of SCP-R-002 cannot
# silently break SCP-R-004. Closes 020L R1 SAFE-MAJ-001.
#
# If a future PR lifts these helpers to `policies/scp_common.rego` as
# cross-rule shared helpers (see §10 [deferrable] resolution), SCP-R-004
# switches to `scp_is_waiver_payload` / `scp_has_nonempty_string` in the
# same PR — the lift-and-switch is a single atomic change.
scp_r_004_is_waiver_payload if {
  is_array(input)
  count(input) > 0
}

scp_r_004_is_waiver_payload if {
  is_array(input)
  count(input) == 0
}

scp_r_004_has_nonempty_string(entry, key) if {
  value := object.get(entry, key, null)
  is_string(value)
  value != ""
}

# Match: any URL substring with HTTP(S) scheme + at least one non-whitespace
# char. Accepts non-GitHub URLs (GitLab, Linear, Atlassian, internal wikis
# with a stable URL, etc.) — the v1.1.0 baseline is "any URL is sufficient
# evidence that a durable decision artifact exists". A future stronger
# variant (e.g. SCP-R-005) could narrow to a recognised issue-tracker
# domain list. HTTP+HTTPS both accepted per §10 [BLOCKING] resolution.
scp_r_004_has_url(text) if {
  regex.match(`https?://[^\s]+`, text)
}

scp_r_004_raw_findings contains finding if {
  scp_r_004_is_waiver_payload
  some index, entry in input
  is_object(entry)
  scp_r_004_has_nonempty_string(entry, "reason")
  reason := object.get(entry, "reason", "")
  not scp_r_004_has_url(reason)
  finding := {
    # Phase-2 implementation must enrich this message to match the §3.3
    # annotation contract verbatim: include entry rule_id/finding_id via
    # `object.get(entry, "rule_id", "")` + `object.get(entry, "finding_id", "")`,
    # and truncate the entry's reason to 80 chars with trailing "…" per §3.3.
    # The simplified message below is the sketch's PoC text — Phase-2
    # implementation enriches it.
    "message": sprintf(
      "waiver entry %d reason field must contain a decision-artifact URL (issue, PR, or decision log entry)",
      [index],
    ),
    "rule_id": scp_r_004_rule_id,
    "file": "output/findings/waivers.json",
    "remediation_url": scp_r_004_remediation_url,
  }
}

# Public deny rule — fires on raw findings not suppressed by waiver or
# rule-config disable. At WARN BASELINE (v1.1.0), the workflow treats
# SCP-R-004 deny output as `::warning::` annotations rather than `::error::`
# — the deny rule itself fires; the workflow step "Emit per-rule warning
# annotations" adds SCP-R-004 to the warn-class set (Phase-2 deliverable
# per the "Warn-baseline workflow integration" paragraph below). The two
# warn rules below emit suppression-observability records ONLY (matching
# the SCP-R-001/002/003 pattern); they do NOT emit raw warn-baseline
# annotations. The promotion proposal (v2.0.0+) flips the workflow's
# warn-class set so SCP-R-004 deny is treated as `::error::` again.
deny contains output if {
  some finding in scp_r_004_raw_findings
  not scp_active_waiver_for(scp_r_004_rule_id)
  not scp_rule_config_disabled(scp_r_004_rule_id)
  output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability: an active waiver against SCP-R-004 silenced
# the deny. Emits one record per waiver-suppression event.
warn contains record if {
  count(scp_r_004_raw_findings) > 0
  some w in scp_waivers
  object.get(w, "rule_id", "") == scp_r_004_rule_id
  not scp_waiver_expired(w)
  record := {
    "kind": "waiver",
    "rule_id": scp_r_004_rule_id,
    "waiver_id": object.get(w, "waiver_id", ""),
    "finding_id": object.get(w, "finding_id", ""),
    "expires_at": object.get(w, "expires_at", ""),
    "file": "output/findings/waivers.json",
    "msg": sprintf(
      "%s suppressed by waiver (waiver_id=%s, expires_at=%s)",
      [scp_r_004_rule_id, object.get(w, "waiver_id", ""), object.get(w, "expires_at", "")],
    ),
  }
}

# Suppression-observability: rule-config disable silenced the deny.
warn contains record if {
  count(scp_r_004_raw_findings) > 0
  scp_rule_config_disabled(scp_r_004_rule_id)
  cfg := scp_rule_config_entry(scp_r_004_rule_id)
  record := {
    "kind": "rule_config",
    "rule_id": scp_r_004_rule_id,
    "reason": "rule-config override",
    "expires_at": object.get(cfg, "expires_at", ""),
    "msg": sprintf(
      "%s suppressed by .scp/rule-config.yaml (expires_at=%s)",
      [scp_r_004_rule_id, object.get(cfg, "expires_at", "")],
    ),
  }
}
```

Reuses from `policies/scp_common.rego` (per the loaded-into-`main` pattern documented at the top of that file): `scp_active_waiver_for`, `scp_waiver_expired`, `scp_rule_config_disabled`, `scp_rule_config_entry`, `scp_waivers`. SCP-R-004 does NOT call any `scp_r_002_*` predicates directly — it defines its own (semantically identical) guards above to prevent silent-bypass on a SCP-R-002 refactor (see 020L R1 SAFE-MAJ-001 closure).

**Warn-baseline workflow integration** — the SCP policy-check workflow's warn-emission step needs to recognise SCP-R-004 deny output as warning-class. Phase-2 deliverable: `.github/workflows/policy-check.yml` "Emit per-rule warning annotations" step adds SCP-R-004 to the warn-class set OR (preferred) uses a generic warn-class enumeration. The two `warn` rules above emit suppression-observability records (matching SCP-R-001/002/003); they do NOT emit raw-finding annotations — that is the workflow's responsibility at the warn-baseline tier.

## 4. False-positive surface

Three FP classes:

### FP-1 — Pre-existing waivers without URLs

**Class.** Every waiver currently in any adopter's waivers.json that has a free-text `reason` becomes a warn at v1.1.0 cut.

**Estimated rate.** At SCP-self today, the testdata waivers under `policies/testdata/` are the primary corpus and most use placeholder `reason` text. For estate adopters, expect 5–30 waivers per repo at v1.1.0 cut (varies). Per 100 PRs, the warn fires once per PR that touches a waivers.json containing a non-URL waiver — but the warn does NOT block merge.

**Recommended adopter response.** Either (a) amend the waiver's `reason` field to include a URL on the next PR that touches the waiver (gradual cleanup); or (b) `.scp/rule-config.yaml disable: true` for SCP-R-004 with `expires_at: <90-day window>` to give the team a transition period; or (c) bulk-amend all existing waivers to add URLs in one cleanup PR.

### FP-2 — Adopters with non-URL governance artifacts

**Class.** Adopter governance flow uses an artifact that does not have a public URL — e.g. an internal wiki page accessed only via VPN, or a Slack message archive that is not externally URL-addressable, or a verbal-only governance forum.

**Estimated rate.** Estate-wide: low (≤5% of adopters; the estate's governance pattern documented in `MEMORY.md` `project_estate_structure.md` and `reference_ct_notifications.md` already points to URL-addressable artifacts — `~/Projects/control-tower/governance/docs/notifications/` files have GitHub raw URLs). Per 100 PRs: rare.

**Recommended adopter response.** Use a stable URL for the artifact even if it 404s for outside-VPN users (e.g. `https://wiki.internal/waivers/2026-05-01`) — the rule enforces "a URL exists", not "the URL is publicly resolvable". Or `.scp/rule-config.yaml disable: true` indefinitely with a justification documenting the governance constraint.

### FP-3 — URL pointing at an unrelated artifact

**Class.** A waiver entry's `reason` contains a URL but the URL does not point at an issue/PR/decision artifact — e.g. `reason: "see https://example.com for context"` where example.com is a marketing page.

**Estimated rate.** Adversarial-only: a reviewer who actively wants to bypass the rule's spirit can construct a meaningless URL. Honest-actor rate: very low. Per 100 PRs: ≤1.

**Recommended adopter response.** Out of scope for SCP-R-004 v1.1.0. The rule's promise is "a URL exists in the reason"; "the URL points at a decision artifact" is a stronger predicate that requires URL-content fetching, which would (a) introduce a network dependency in the gate, (b) couple the gate to issue-tracker authentication, and (c) significantly enlarge the bypass surface. A future SCP-R-005 could narrow to a recognised issue-tracker domain allowlist (github.com/issues, gitlab.com/-/issues, linear.app, atlassian.net/browse, internal-prefix/...) but that proposal would need its own RFC + deprecation ramp.

## 5. Bypass surface

**None — uses existing scp_bypass three-gate + rule-config disable mechanisms.**

- **No new `.scp/rule-config.yaml` key.** Adopters use the existing `disable: true` + `justification` + `expires_at` shape per `schemas/rule-config.schema.json`.
- **No new `scp_bypass: <variant>` flag.** The existing single-flag bypass + three-gate (CODEOWNERS approval + bypass-pairing.sh check + workflow-recorded readback) covers SCP-R-004 identically to SCP-R-001/002/003.
- **No new per-finding waiver shape.** The existing `schemas/waiver.schema.json` shape (`{rule_id, reason, approved_by, created_at, expires_at, ...}`) is unchanged. A waiver against SCP-R-004 itself is shaped identically to a waiver against any other SCP-R-NNN rule. **Important:** such a meta-waiver MUST itself contain a URL in its `reason` field (e.g. `reason: "waiving SCP-R-004 for legacy waivers per https://github.com/.../issues/NNN"`) — otherwise the meta-waiver is ALSO a raw finding for SCP-R-004 (the rule fires on every URL-less waiver entry, including waivers targeting SCP-R-004). An operator who cannot supply a URL in the meta-waiver's reason should instead use `.scp/rule-config.yaml disable: true` for the transition period.

### Implicit exclusion set (per 020H.1 R1 SAFE-MAJ-002 closure)

Reviewers MUST verify the exemption set is intentional and does NOT create an unreviewed bypass-by-omission. SCP-R-004 returns `allow` (does NOT fire raw finding) on:

1. **Input is not a JSON array** (`is_array(input) == false`). Conftest invokes every rule against every file. Files like services.yml, expected-annotations.json, package.json, manifest.yml etc. are object-rooted or string-rooted; SCP-R-004 no-ops on them. **Intentional.** Path-scope tightening is TF-008 v1.1+ work that benefits SCP-R-004 the same way it benefits SCP-R-002.
2. **Input is an empty JSON array** (`is_array(input) == true && count(input) == 0`). Empty waivers.json is a valid state (no waivers configured); SCP-R-004 has nothing to evaluate. **Intentional.**
3. **Waiver entry `reason` field is absent or empty** (`scp_r_004_has_nonempty_string(entry, "reason") == false`). SCP-R-002 already emits a deny on this case (missing required key from its `scp_r_002_required_keys` set); SCP-R-004 does not double-fire. **Intentional, prevents redundant noise.**
4. **Waiver entry `reason` contains at least one HTTP(S) URL** (`regex.match(`https?://[^\s]+`, reason) == true`). The rule's positive case. **Intentional.**
5. **Residual known bypass — reason contains a syntactically valid URL that does not point at a decision artifact.** The regex matches any `https?://` substring including `https://x` or `https://example.com`. SCP-R-004 enforces "a URL exists in the reason field", NOT "the URL resolves to a reviewable decision artifact". Adversarial adopters can construct a meaningless URL to satisfy the rule (also documented at §4 FP-3 as adversarial-only). This is the rule's known v1.1.0 honest-posture limitation; reviewers approving on the basis of `Bypass-surface non-empty: false` should treat the front-matter declaration as "no NEW bypass mechanism is introduced", not as "no possible bypass exists". A future SCP-R-005 proposing a recognised-domain allowlist (github.com/issues, gitlab.com/-/issues, linear.app, atlassian.net/browse, internal-prefix/...) would move this from residual to closed; that proposal would require its own RFC + deprecation ramp. Closes 020L R1 SAFE-MAJ-002.

The exclusion set has no implicit bypass-by-omission: every case is either covered by SCP-R-002 (case 3), a structural no-op (cases 1+2), the rule's success path (case 4), or an explicitly-named residual bypass with a forward-looking closure path (case 5).

## 6. Conflict-gate strategy

### 6.1 Python evaluator parity

The match conditions are trivially expressible in Python today. The conflict-gate adapter (`tests/conflict_gate/adapter.py` per `STATUS.md` reference) handles array-rooted inputs identically to SCP-R-002. The SCP-R-004 Python evaluator implementation is:

```python
import re
from typing import Any

URL_PATTERN = re.compile(r"https?://\S+")

def evaluate_scp_r_004(payload: Any) -> list[dict]:
    findings = []
    if not isinstance(payload, list) or len(payload) == 0:
        return findings
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            continue
        reason = entry.get("reason", "")
        if not isinstance(reason, str) or reason == "":
            continue
        if not URL_PATTERN.search(reason):
            findings.append({
                "rule_id": "SCP-R-004",
                "message": f"waiver entry {index} reason field must contain a decision-artifact URL (issue, PR, or decision log entry)",
                "file": "output/findings/waivers.json",
            })
    return findings
```

Both engines use the same regex pattern syntax (`https?://\S+` — `\S` = non-whitespace, matches both engines' regex flavor). Disagreement risk is LOW.

### 6.2 Conflict-gate fixture corpus

Phase-2 deliverable: `tests/conflict_gate/scp-r-004/{allow,deny}/` with the following fixtures (every shared fixture passes through `tests/conflict_gate/adapter.py`):

**`allow/`** (all should NOT fire raw finding):
- `empty-array.json` — `[]`
- `single-waiver-with-github-issue-url.json` — one entry with `reason: "Approved per https://github.com/jrnb2024/standards-control-plane-/issues/42 — investigation pending"`.
- `single-waiver-with-github-pr-url.json` — one entry with `reason: "Per design discussion in https://github.com/jrnb2024/standards-control-plane-/pull/78"`.
- `single-waiver-with-non-github-url.json` — one entry with `reason: "See https://linear.app/team/issue/ABC-123 for tracker"` (estate-flexibility validation).
- `single-waiver-with-decision-log-url.json` — one entry with `reason: "Ratified per D-022 — see https://github.com/jrnb2024/standards-control-plane-/blob/main/docs/DECISIONS.md"`.
- `multi-waiver-all-with-urls.json` — three entries, each with a different valid URL.
- `waiver-with-reason-absent.json` — one entry with `reason` field absent. (SCP-R-002 will deny on this; SCP-R-004 should NOT fire — verifies non-overlap.)
- `waiver-with-reason-empty-string.json` — one entry with `reason: ""`. (SCP-R-002 will deny; SCP-R-004 should NOT fire.)

**`deny/`** (all should fire raw finding — at warn the workflow surfaces as `::warning::`):
- `single-waiver-no-url.json` — one entry with `reason: "approved by Jim"`.
- `single-waiver-with-bare-domain.json` — one entry with `reason: "see github.com for context"` (no scheme — should NOT match the URL pattern; should fire).
- `multi-waiver-mixed.json` — three entries; one has a URL, two don't. Should fire 2× (one finding per missing-URL entry).
- `single-waiver-with-text-mentioning-url.json` — one entry with `reason: "discussed in slack — url tomorrow"`. The literal word "url" is not a URL pattern match; should fire.

### 6.3 Conflict-gate disagreement risk

LOW for the ASCII fixture corpus enumerated at §6.2. Both regex engines (Rego's RE2-based `regex.match` and Python's `re.search`) handle the `https?://\S+` pattern identically for ASCII inputs. Conflict-gate flap risk on the SCP self-dogfood gate is therefore minimal; if a flap surfaces during Phase-2 implementation, it would emit `SCP-E005` and merge-block, prompting an amending decision row per ADOPT-001 §12.7.7.

**Unicode-whitespace caveat (TF-020L-001).** Python 3 `re` treats `\S` as Unicode-aware by default for `str` patterns (per PEP 461 / `re.UNICODE`), so Python's `\S` does NOT match Unicode whitespace characters such as U+00A0 (NO-BREAK SPACE) or U+2003 (EM SPACE). OPA's RE2-based `[^\s]` set is restricted to ASCII whitespace `[ \t\n\r\f\v]` only — it does NOT include Unicode whitespace. A waiver `reason` string containing a URL terminated by a Unicode whitespace character (e.g. `reason: "see https://example.com/x for context"`) would parse differently: OPA would consume further into the string while Python would stop earlier. For the §6.2 ASCII fixture corpus this divergence is irrelevant. **Closure path:** TF-020L-001 — Phase-2 implementation monitors the SCP self-dogfood gate for any `SCP-E005` flap on a Unicode-whitespace input; if observed, anchor the regex pattern to ASCII-only equivalent in both engines (e.g. `https?://[\x21-\x7e]+` for printable ASCII excluding whitespace) and add a fixture to §6.2. Close TF-020L-001 as no-op if no divergence surfaces during the warn-baseline observation window.

## 7. Estate-cascade considerations

The six named estate adopters per WP-SCP-024 plan and `MEMORY.md` `project_scp_control_plane_architecture.md`:

| Adopter | Likely warn opt-in at v1.1.0? | Notes |
|---|---|---|
| FLA (`fashion-labelling-agent`) | Immediately at warn | Per `reference_fla_gold_standard.md` — gold-standard reference, likely opts into every governance rule by default. May need a 30-day transition to add URLs to legacy waivers. |
| PIM | Immediately at warn | Per `project_auth_conformance_state.md` — already on the canonical BFF pattern + auth-conformance is complete. Governance posture is mature. |
| recommender | Likely 30-day transition | Less governance-active; may need a short rule-config disable window while existing waivers are amended. |
| shopify-app | Likely 60-day transition | Smaller team; benefit from a longer transition window. |
| mapp-doc-agent | Immediately at warn | Documentation-focused; URLs are natural to the domain. |
| control-tower | Immediately at warn | Per `project_estate_structure.md` + `reference_ct_notifications.md` — CT governance flow already references issue/PR URLs in `~/Projects/control-tower/governance/docs/notifications/`. |

### Estate-wide D-NNN

A coordination D-NNN ("estate adopters MAY disable SCP-R-004 for up to 90 days post-v1.1.0 to amend legacy waivers; thereafter the rule is expected at warn baseline across the estate") would be filed as part of the v1.1.0 cut (Phase-2 deliverable), NOT as part of this proposal merge. Filing the D-NNN now would presume the rule's acceptance before the 48h window closes.

## 8. Test plan

### 8.1 Conftest test fixtures

Phase-2 deliverable: `policies/tests/scp_r_004_test.rego` covering:

- `test_allow_empty_array` — input is `[]`, raw findings count is 0.
- `test_allow_single_waiver_with_github_issue_url` — single entry, raw findings count is 0.
- `test_allow_single_waiver_with_non_github_url` — non-GitHub URL accepted.
- `test_allow_multi_waiver_all_with_urls` — three entries, all with URLs, raw findings count is 0.
- `test_deny_single_waiver_no_url` — single entry without URL, raw findings count is 1, finding's `rule_id == "SCP-R-004"`.
- `test_deny_multi_waiver_mixed` — three entries, two without URLs, raw findings count is 2.
- `test_no_op_on_object_rooted_input` — input is `{...}` (not array), raw findings count is 0.
- `test_no_op_on_string_rooted_input` — input is `"some text"`, raw findings count is 0.
- `test_no_op_on_null_input` — input is `null`, raw findings count is 0.
- `test_no_op_on_waiver_with_reason_absent` — entry lacks `reason` field; SCP-R-004 does NOT fire (SCP-R-002's deny path covers this).
- `test_no_op_on_waiver_with_empty_reason` — `reason: ""`; SCP-R-004 does NOT fire.
- `test_waiver_suppresses_via_scp_r_004_waiver` — meta-recursive: a waiver against SCP-R-004 itself suppresses the warn record (uses `scp_active_waiver_for("SCP-R-004")`).
- `test_rule_config_disable_suppresses` — `.scp/rule-config.yaml` `disable: true` suppresses, emits the rule-config kind warn record per `scp_rule_config_disabled`.
- `test_expired_waiver_does_not_suppress` — fail-closed per `scp_waiver_expired`.

### 8.2 Conflict-gate fixtures

Per §6.2 above. Phase-2 deliverable. The conflict-gate (`.github/workflows/conflict-gate.yml`, slice 020N hash-pinned) will run both engines against the corpus and flap-or-pass the gate.

### 8.3 Workflow-selftest harness coverage

Existing harnesses in `tests/workflow/<harness>/` enumerate `data.main.warn[_]` records (per the existing SCP-R-001/002/003 warn-emission flow). SCP-R-004 follows the same shape; no new harness needed. Phase-2 deliverable: extend an existing harness fixture set to include a SCP-R-004 warn case if the warn-emission step proves to need rule-specific handling (anticipated NOT to be required given the generic `warn` rule shape used by all existing rules).

### 8.4 Canary update

NOT required for Phase-2 v1.1.0 cut. SCP-R-004 fires at warn baseline only — it does not change adopter PR merge behaviour (no deny path active). The existing canary suite (`canary/deliberate-violation-pre`, `canary/waived-violation`, `canary/rule-config-disabled`) covers the deny + waiver-suppressed + rule-config-suppressed triad against SCP-R-001. A new SCP-R-004 canary would be redundant.

A future MAJOR promotion (warn → deny default, v2.0.0+) WILL require a `canary/scp-r-004-deny` fixture to exercise the deny path; that's a separate proposal's Phase-2 deliverable.

## 9. Migration / rollout

Per `policies/VERSIONING.md`:

- **New rule at warn → MINOR bump.** v1.0.1 → **v1.1.0**.
- **No `policies/deprecations.yaml` entry needed.** Per VERSIONING.md, deprecation entries are required only for surfaces being deprecated (the rule additions section is silent on entries; the empty register at v1.0.0 confirms no entry was needed for SCP-R-001/002/003 either at their original cut).
- **No release-gate refusal at v1.1.0 cut.** The release-gate (`.github/workflows/release-gate.yml`, slice 020H.3) refuses tag-cuts only on deprecation-ramp violations or expired SCP-self rule-config entries. A rule-add at warn does not trigger either condition.
- **No merge-time `docs/DECISIONS.md` D-NNN required for SCP-R-004 itself.** Per `README.md` §3 Merge, a D-NNN is required only when "the rule introduces a new domain or escalates an existing rule's threshold". SCP-R-004 operates within the SAME domain as SCP-R-002 (the waivers domain — both rules read from the waivers payload, both target waiver-shape governance). It is an additive constraint on existing waiver shape, not a new domain or threshold escalation. Therefore no D-NNN is filed at merge time. (Phase-2 may file an estate-wide coordination D-NNN per §7 to document the 90-day adopter transition window — that filing is independent of the merge-time D-NNN condition.)

### Adopter-side migration steps beyond standard SHA-pin bump

When adopters bump their SCP federation primitive pin from v1.0.x to v1.1.0:

1. The next PR to touch the adopter's waivers.json (or the next PR generally if the workflow is enumerating all waivers, which is the common case) will surface SCP-R-004 warn annotations on every waiver entry whose `reason` lacks a URL.
2. Adopter response options (per §4):
   - Amend each waiver's `reason` to include a URL on its next-touch PR (gradual cleanup).
   - Add `.scp/rule-config.yaml disable: true` for SCP-R-004 with `expires_at: <90-day window>` and `justification: "transition window — amending legacy waivers to include URLs"`.
   - Bulk-amend all waivers in one cleanup PR.
3. After the warn period, the operator (or estate-wide D-NNN) decides whether to promote SCP-R-004 to deny default. Earliest plausible promotion: v2.0.0.

ADOPT-001 maintenance: Phase-2 deliverable adds a §12.7.X subsection "Adopter response to SCP-R-004 warn annotations" documenting the three response options above.

## 10. Open questions

- **`[BLOCKING]`** Should the URL pattern require an issue-tracker domain (github.com, gitlab.com, linear.app, atlassian.net) or accept any HTTP(S) URL? **Resolution (proposal):** accept any HTTP(S) URL for estate-flexibility (per §3.4 commentary + §4 FP-3). A future stronger variant (SCP-R-005) could narrow. *(Reviewers: confirm or reject this resolution before approving.)*
- **`[BLOCKING]`** Should the rule fire on SCP-R-002 raw findings (only when the waiver entry would otherwise be valid) or independently? **Resolution (proposal):** independently, because SCP-R-002's `scp_r_002_has_nonempty_string(entry, "reason")` guard already prevents double-firing on the missing-`reason` case (verified at §3.1 "Coexistence with SCP-R-002"). *(Reviewers: confirm.)*
- **`[BLOCKING]`** Is the regex `https?://\S+` (matching anywhere in the `reason` string) the right pattern, or should we anchor to start, or require a longer minimum match length, or reject `reason` strings where the URL is the entire content (i.e. require some explanation alongside the URL)? **Resolution (proposal):** unanchored, no minimum, no required-explanation. The rule's promise is "a URL exists"; richer content checks are outside scope. *(Reviewers: confirm.)*
- **`[BLOCKING]`** Should we accept HTTP (not just HTTPS) URLs? **Resolution (proposal):** accept both at v1.1.0 — the regex `https?://` covers both. Internal-network artifacts may be served over HTTP; rejecting HTTP would create FP class FP-2 unnecessarily. *(Reclassified from `[deferrable]` per 020L R1 COR-MAJ-002: the HTTP-vs-HTTPS boundary changes which waiver entries fire the rule and therefore changes match scope, qualifying as `[BLOCKING]` per RULE-TEMPLATE.md §10. The pre-resolution stands; reviewers confirm.)*
- **`[deferrable]`** Should the truncation cutoff in the warn message body be 80 chars or longer? **Resolution (proposal):** 80 chars with trailing `…`. *(Implementation detail.)*
- **`[deferrable]`** Should the rule emit ONE finding per missing-URL waiver entry, or aggregate to ONE finding per file with a count? **Resolution (proposal):** one per entry, mirroring SCP-R-002's per-entry shape — keeps annotation actionability per-entry. *(Implementation detail.)*
- **`[deferrable]`** Should `policies/scp_common.rego` gain a shared `scp_has_url` predicate so a future SCP-R-005 / SCP-R-006 can reuse it? **Resolution (proposal):** defer to Phase-2 implementation — if `scp_r_004_has_url` is the only caller at v1.1.0, no need to lift to common; if Phase-2 adds a second caller, lift in the same PR (also coordinates with the SAFE-MAJ-001 closure plan to lift `scp_r_004_is_waiver_payload` + `scp_r_004_has_nonempty_string` if cross-rule sharing is wanted). *(Implementation detail.)*

A proposal with unresolved `[BLOCKING]` questions does NOT meet quorum even with one CODEOWNER approval (per `RULE-TEMPLATE.md` §10 + 020H.1 R1 SAFE-nit-008 closure). The four `[BLOCKING]` questions above are pre-resolved by the proposal text; reviewer approval implicitly ratifies the resolutions, OR a reviewer comment changes one and triggers a proposal revision.

## 11. References

### Cited findings

- The audit-trail gap described in §2 — manifest in any pre-v1.1.0 waivers.json with free-text `reason`. No issue number; the gap is structural rather than a single incident.

### Related rules

- **SCP-R-002** (`policies/SCP-R-002.rego`) — waiver shape enforcement. Coexistence guarantee documented at §3.1 + §3.4.
- **SCP-R-001** (`policies/SCP-R-001.rego`) — services.yml `auth.mode` lifecycle. Different domain; SCP-R-004 inherits the `scp_active_waiver_for` + `scp_rule_config_disabled` plumbing pattern.
- **SCP-R-003** (`policies/SCP-R-003.rego`) — vendoring attestation. Different domain; same plumbing pattern.

### Related decisions

- **D-022** (`docs/DECISIONS.md`) — federation primitive adoption (referenced for the BS-5 closure rationale; see `README.md` §References).
- **D-031** (`docs/DECISIONS.md`) — adopt 020K personal-account / single-operator CODEOWNERS path. Quorum=1 per single-operator mode.
- **D-036** (`docs/DECISIONS.md`) — `policies/VERSIONING.md` semver contract + RFC-lite process; this proposal is the first instance of that process.

### ADOPT-001 sections

- **§12.7.7** — SCP-EXXX codespace (closed infrastructure set; rules do NOT claim their own SCP-E codes). SCP-R-004 follows this constraint.
- **§12.7.X (NEW, Phase-2 deliverable)** — adopter response to SCP-R-004 warn annotations. Authored as part of the v1.1.0 cut, NOT as part of this proposal merge.

### RFC infrastructure

- `docs/reviews/rule-proposals/README.md` — RFC-lite process. Authored at slice 020H.1 (PR #78, 2026-05-01).
- `docs/reviews/rule-proposals/RULE-TEMPLATE.md` — copy-paste skeleton this proposal followed.
- `policies/VERSIONING.md` — semver contract governing the v1.1.0 MINOR bump target for this rule (see §3.2 + §9 for the warn-baseline new-rule mapping).

### Schemas

- `schemas/waiver.schema.json` — single-waiver shape. Required `reason` with `minLength: 1`.
- `schemas/waivers-file.schema.json` — array-of-waivers shape. SCP-R-004 fires on this top-level shape.
- `schemas/rule-config.schema.json` — adopter rule-config shape. SCP-R-004 disable path uses this.

### Slice / programme references

- `STATUS.md` Post-Threshold-A backlog "WP-SCP-022 proposal-queue" — the backlog item this slice closes.
- `docs/reviews/WP-SCP-022/dispatches/020l/DISPATCH-NOTE.md` — slice 020L dispatch note (this proposal's Phase-1 surface).
- `docs/reviews/WP-SCP-022/CONTINUATION-PROMPT-2026-05-02-pm.md` — recommended this rule as the dogfood candidate.
