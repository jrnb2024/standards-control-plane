# Autonomous-run prompt — WP-SCP-028 auth-canonical conformance Phase 1

**Drafted:** 2026-05-29 (concurrent with D-058 ratification PR)
**Plan-doc anchor:** `docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md`
**Strategic anchor:** `docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md`
**Session character:** Single long autonomous run via Pattern 3 (Claude Code autonomous session per D-057). **NO HOLD-FOR-OPERATOR gates within the run.** Operator-attended controls are pre-flight (dispatch bootstrap + prereq verification) and post-run (v1.4.0 cut + cohort cascade ceremony).

---

## §0 Operator-attended pre-launch (THIS IS THE ONLY MANUAL STEP)

Before launching the autonomous session, the operator:

### 0.1 Verify prereqs

Run from a normal terminal:

```bash
cd ~/Projects/standards-control-plane

# 1. Verify D-058 + WP-SCP-028 plan-doc + coordination memo are on main
git fetch origin main
git log --oneline origin/main -3
# Expect: latest commit is D-058 ratification PR merge

# 2. Verify CT added the protected_primitives block to auth-contract-v1.yaml
#    (THIS IS THE ONE HARD CT PREREQ.)
gh api repos/jrnb2024/control-tower/contents/contracts/auth-contract-v1.yaml --jq '.content' | base64 -d | grep -A 5 "^protected_primitives:"
# Expect: a block declaring python/typescript/go protected-symbol lists
# If absent, HALT — SCP-R-010 (auth-canonical-import-fence) cannot be authored.
# (Handoff prompt for CT: ~/Projects/standards-control-plane/docs/coordination/2026-05-30-WP-SCP-028-CT-prereqs-handoff-prompt.md)

# 3. Verify CT's auth-contract-v1.yaml.sig.bundle verifies via cosign
#    THIS is the real verification anchor — NOT the manifest_sha256 field.
#    (If you have cosign + the bundle locally:
#       cosign verify-blob --bundle auth-contract-v1.yaml.sig.bundle auth-contract-v1.yaml
#     succeeds. A drifted manifest_sha256 does NOT block — it's a freshness hint,
#     not the anchor. Do NOT gate on it.)

# 4. Verify acc-hook is live (D-057 cardinal pre-flight)
python3 -c "import json,pathlib; p=pathlib.Path('.claude/settings.json'); d=json.loads(p.read_text()); print('hooks:', list(d.get('hooks',{}).keys()))"
# Expect: hooks: ['PreToolUse']
```

If ANY of steps 1-3 fail: stop. Do not launch the autonomous session. CT-side prereqs must close first per the coordination memo at `docs/coordination/2026-05-29-estate-canonicals-cheap-shape.md` §5.

### 0.2 Bootstrap the session-start dispatch

Per D-057's Pattern-3 + dispatch ceremony, the operator declares the session's source-write scope BEFORE launching the Claude Code session. From the same normal terminal:

```bash
cd ~/Projects/standards-control-plane
scripts/operator/scp-pattern3-dispatch.sh \
    "policies/SCP-R-009.rego" \
    "policies/SCP-R-010.rego" \
    "policies/SCP-R-011.rego" \
    "policies/scp_common.rego" \
    "policies/rule-config.yaml" \
    "policies/VERSIONING.md" \
    "schemas/canonical-sdk-versions.schema.json" \
    "schemas/auth-contract-v1.schema.json" \
    "schemas/rule-config.schema.json" \
    "tests/policies/test_SCP-R-009*" \
    "tests/policies/test_SCP-R-010*" \
    "tests/policies/test_SCP-R-011*" \
    "tests/fixtures/auth-canonical/**" \
    "version-manifest.json" \
    "STATUS.md" \
    "docs/reviews/WP-SCP-028/**"
```

**Critical (D-057 §4 self-escalation guard):** none of these paths covers `.acc/active-dispatch.json` itself. The script will refuse blanket globs by design.

### 0.3 Launch the autonomous Claude Code session

Open a fresh Claude Code session in `~/Projects/standards-control-plane` (project root = SCP repo; the hook is live and will gate source writes to the declared scope). Paste:

```
Read and execute docs/continuation-prompts/2026-05-30-WP-SCP-028-auth-canonical-autonomous.md
```

### 0.4 Teardown (at end-of-run)

After the autonomous session reports completion + the operator-action message:

```bash
cd ~/Projects/standards-control-plane
scripts/operator/scp-pattern3-dispatch.sh --teardown
```

This is the D-057 ceremony's mandatory final step (removes `.acc/active-dispatch.json` so a later session can't ride it). The autonomous session will REMIND the operator in its close-out message.

---

## §1 Autonomous session — Phase 0 pre-flight (deterministic)

The autonomous session runs the following at start. **HALT cleanly** with operator-action message if any fail.

### 1.1 Verify hook + dispatch state

```bash
# Hook live
test -f .claude/settings.json && python3 -c "
import json,sys
d=json.load(open('.claude/settings.json'))
hooks=d.get('hooks',{})
assert 'PreToolUse' in hooks, f'acc-hook NOT live; expected PreToolUse, got {list(hooks.keys())}'
print('hook: live')
"

# Dispatch present + reasonable
test -f .acc/active-dispatch.json && python3 -c "
import json
d=json.load(open('.acc/active-dispatch.json'))
assert 'scope_boundary' in d
assert len(d['scope_boundary']) >= 10, f'scope unexpectedly narrow ({len(d[\"scope_boundary\"])} entries); expected ≥10 for WP-SCP-028'
# Sanity-check no self-escalation
assert '.acc/active-dispatch.json' not in d['scope_boundary']
assert '**' not in d['scope_boundary']
print(f'dispatch: {d[\"dispatch_id\"]}; scope_boundary={len(d[\"scope_boundary\"])} entries')
"
```

HALT if either fails.

### 1.2 Re-verify CT prereqs (defense-in-depth vs §0.1)

```bash
# THE ONE HARD CT PREREQ: protected_primitives block present.
curl -sL "https://raw.githubusercontent.com/jrnb2024/control-tower/main/contracts/auth-contract-v1.yaml" -o /tmp/auth.yaml
if ! grep -q "^protected_primitives:" /tmp/auth.yaml; then
    echo "HALT: contracts/auth-contract-v1.yaml lacks protected_primitives block (SCP-R-010 cannot be authored)"
    exit 1
fi

# VERIFICATION ANCHOR: the .sig.bundle (cosign), NOT manifest_sha256.
curl -sL "https://raw.githubusercontent.com/jrnb2024/control-tower/main/contracts/auth-contract-v1.yaml.sig.bundle" -o /tmp/auth.sig.bundle
if command -v cosign >/dev/null 2>&1; then
    cosign verify-blob --bundle /tmp/auth.sig.bundle /tmp/auth.yaml \
        || { echo "HALT: auth-contract-v1.yaml.sig.bundle does NOT cosign-verify (fail-closed)"; exit 1; }
else
    echo "WARN: cosign not installed locally; verification deferred to the policy-check workflow's signed-fetch step. Proceed (the gate verifies at evaluation time)."
fi

# NOTE: manifest_sha256 currency is deliberately NOT checked. It is a freshness
# hint that may legitimately drift (cleared on CT's FUP-CT-MANIFEST-CRON-REFRESH-001
# roadmap or as a side effect of the protected_primitives re-sign). It is NOT the
# verification anchor and does NOT block WP-SCP-028.
```

### 1.3 Re-read load-bearing context

Confirm understanding (don't re-author):

- `docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md` — strategic direction; LINKAGE-not-VALUES; 4-artefact publish contract; enforcement-plane-not-control-plane
- `docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md` — this WP's binding plan
- `docs/decisions/D-049-design-system-policy-layer-adoption-2026-05-19.md` — architectural inheritance (LINKAGE discipline; OPA sweet-spot anti-scope)
- `policies/SCP-R-006.rego` — prototype shape; same workflow-input materialisation pattern
- `policies/scp_common.rego` — shared helpers
- `policies/VERSIONING.md` — WARN_BASELINE_RULES set extension target

---

## §2 Phase 1 — Schemas

Author the three schema files. Order: schemas before rules (rules will reference schema-validated structures).

### 2.1 `schemas/canonical-sdk-versions.schema.json`

Match CT's published shape (verify against `/tmp/csv.yaml` from §1.2). Required keys:
- `schema_version` (string; semver)
- `manifest_sha256` (string; 64-char hex)
- `signed_at` (RFC3339)
- `signer` (string)
- `packages` (object keyed by language: `python`, `typescript`, `go`)
  - per language: object keyed by package-name → `{minimum_version, current_version, deprecated_versions[]}`

### 2.2 `schemas/auth-contract-v1.schema.json`

Match CT's published shape (verify against `/tmp/auth.yaml`). Required keys:
- `claim_shape_version` (string; semver)
- `canonical_issuer_pattern` (string; regex)
- `canonical_audience_list` (string array)
- `protected_primitives` (object keyed by language → array of forbidden symbol names)

### 2.3 `schemas/rule-config.schema.json` — extend

Add 3 new opt-out keys following the existing pattern (mirror SCP-R-006's extension at PR #158):

- `auth-canonical-version-pin-disabled: boolean` (default false)
- `auth-canonical-import-fence-disabled: boolean` (default false)
- `auth-contract-claim-shape-disabled: boolean` (default false)

### 2.4 R1 plan-stage review on schemas (3 lenses)

Dispatch 3 parallel review agents (Explore subagent type or general-purpose):
- **correctness**: do the schemas match CT's actual published shapes? Are required fields actually required? Are types correct?
- **safety_bypass**: can a malformed manifest passing validation defeat the rules? Are there schema-level holes that would let SCP rules vacuously pass on adversarial input?
- **completeness_governance**: do the schemas cover all the rule-input shape needed by SCP-R-009/010/011? Anything missing?

Fold all findings before Phase 2.

---

## §3 Phase 2 — Rules

Author the three Rego rules per `docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md` §3.

### 3.1 `policies/SCP-R-009.rego` — auth-canonical-version-pin

Implementation notes:
- Vacuous-pass guard: if `input.canonical_sdk_versions` absent OR signature verification absent → return zero findings (safe failure mode; same pattern as SCP-R-006)
- Vacuous-pass when adopter doesn't consume ct-auth (no matching import detected in adopter manifest)
- Deny conditions per plan-doc §3.1
- Warn conditions per plan-doc §3.1
- Emit findings in the canonical `SCPFinding` shape (rule_id, severity, message, file, line)

### 3.2 `policies/SCP-R-010.rego` — auth-canonical-import-fence

Implementation notes:
- Reads CT's `auth-contract-v1.yaml.protected_primitives[<lang>]`
- For each file in `input.adopter_changed_files` matching `**/*.{py,ts,tsx,go}`:
  - Substring-detect `import` statement for ct-auth/`@control-tower/auth`/ctauth-go
  - If imported, AST-walk (or regex with named-capture) for function/method declarations matching forbidden symbol set
  - Re-export pattern: regex for `export { primitive as <name> }` (typescript), `<name> = primitive` (python module level), etc.
- Vacuous-pass when no file imports the SDK

### 3.3 `policies/SCP-R-011.rego` — auth-contract-claim-shape

Implementation notes:
- Reads CT's `auth-contract-v1.yaml.canonical_issuer_pattern` (regex) + `claim_shape_version`
- For each file touching Authorization header (substring + AST):
  - Look for `Claims` / `JwtPayload` / equivalent type declaration
  - Check field types match current claim_shape_version
  - Check hardcoded issuer strings (if any) match canonical_issuer_pattern
- Vacuous-pass when no auth handling detected in changed-set

### 3.4 `policies/scp_common.rego` — helpers (extend if needed)

If shared helpers are needed across R-009/010/011 (e.g. `fetch_signed_manifest`, `verify_cosign_signature`, `parse_package_version`), add them here. Keep helpers vacuous-safe (return null/empty on missing input rather than panicking).

### 3.5 R1 plan-stage review on rules (3 lenses; MANDATORY per auth-surface discipline)

Dispatch 3 parallel review agents per rule (9 dispatches total):
- **correctness**: does each rule's logic match its plan-doc §3.x intent? Are deny/warn conditions correctly encoded? Vacuous-pass paths correct?
- **safety_bypass**: can an adopter bypass the rule via path-traversal, encoding tricks, re-export chains, hidden-symbol-shadowing? Are signature checks tight?
- **completeness_governance**: edge cases — empty manifest, malformed JSON, multi-language adopters, monorepo workspaces, vendored-dependency carve-outs?

**Cure-worse R2 trigger** is in effect per the established discipline. If a fix-round introduces worse-than-original behaviour → halt with operator-action.

**REJECT verdict on the safety_bypass lens is a HARD STOP.** This is the auth surface; D-058 + `feedback_orchestrator_auth_surface_plan_review_default.md` make the safety lens load-bearing.

Fold all findings + dispatch fix-rounds as needed. Target: R-FIXPOINT MET across all 3 rules before Phase 3.

---

## §4 Phase 3 — Tests + fixtures

For each rule (R-009/010/011), author test fixtures covering:

### 4.1 Per-rule fixture matrix

| Rule | Fixture category | Expected outcome |
|---|---|---|
| R-009 | adopter pins exact-canonical-version | PASS (no findings) |
| R-009 | adopter pins one MINOR behind | warn |
| R-009 | adopter pins MAJOR behind (downgrade-class) | deny |
| R-009 | adopter doesn't consume ct-auth | vacuous-pass |
| R-009 | manifest signature invalid | fail-closed (deny with `signature_invalid` reason) |
| R-009 | manifest absent (workflow input not materialised) | vacuous-pass |
| R-010 | adopter imports ct-auth, defines no forbidden symbols | PASS |
| R-010 | adopter imports ct-auth, defines `verify_token` function | deny |
| R-010 | adopter re-exports `sign_token as my_sign` | deny |
| R-010 | adopter file doesn't import ct-auth | vacuous-pass |
| R-010 | adopter defines `_legacy_verify_token` (warn condition) | warn |
| R-011 | adopter declares Claims type matching current shape | PASS |
| R-011 | adopter declares Claims type with old `iss: List[str]` | deny |
| R-011 | adopter hardcodes valid issuer | PASS |
| R-011 | adopter hardcodes invalid issuer | deny |
| R-011 | adopter file doesn't touch Authorization | vacuous-pass |

### 4.2 Coverage requirements

- Each rule ≥90% opa coverage (per `policies/SCP-R-001..R-008` precedent)
- `regal lint` clean across all 3 rules
- `opa fmt --diff` clean (no formatting drift)
- Test execution wall-time <10s per rule

### 4.3 Run tests + verify

```bash
# Per-rule coverage
opa test policies/ tests/policies/ --coverage --format=json | jq '.coverage.files'

# regal lint
regal lint policies/

# opa fmt
opa fmt --diff policies/
```

Halt on any failure.

---

## §5 Phase 4 — Bookkeeping

### 5.1 Update `policies/VERSIONING.md`

Extend `WARN_BASELINE_RULES` set to `{"SCP-R-004", "SCP-R-008", "SCP-R-009", "SCP-R-010", "SCP-R-011"}`.

Add documentation block explaining the auth-canonical rules + their D-059 deny-promotion path.

### 5.2 Bump `version-manifest.json`

v1.3.0 → v1.4.0 (MINOR per VERSIONING.md additive-rule guarantee).

### 5.3 Update `docs/DECISIONS.md`

Add a forward-reference row noting D-059 reservation (for D-059 outcome at 4-week observation close). NOT a new ADR; just the reservation pointer.

Bump `**Last Updated:**` to reflect WP-SCP-028 SHIPPED.

### 5.4 Update `docs/BACKLOG.md`

Flip WP-SCP-028 row from OPEN → SHIPPED (or filed-as-Phase-1-shipped if structured per phase).

If WP-SCP-029..036 named-but-not-built roadmap rows don't exist yet, add them with explicit gating-on-authority-publication.

### 5.5 Update `STATUS.md`

Add a chain row to today's chain (or open a new chain for the autonomous-run-completion date) documenting:
- WP-SCP-028 SHIPPED
- v1.4.0 ready-to-cut
- Cohort cascade ready-to-fire via `scripts/operator/scp-wrapper-bump-sweep.sh`
- D-059 reserved for 4-week observation outcome
- `check-invocation-log-entry` triggered via this row

---

## §6 Phase 5 — Operator handoff

Halt with this exact operator-action message:

```
WP-SCP-028 autonomous run complete.

Operator-attended next steps:

1. CUT v1.4.0 release (mirrors v1.3.0 ceremony):
   scripts/operator/cut-release.sh --version v1.4.0 --sha <MERGE_SHA>

2. PROPAGATE to cohort adopters (post-release-tag-push):
   scripts/operator/scp-wrapper-bump-sweep.sh --emit-commands
   # 3 bump PRs: PIM, CT, mapp-doc-agent → v1.4.0 SHA

3. OBSERVE for 4 weeks after all 3 adopters merge their bumps:
   - rule firing rate per adopter per week
   - false-positive count
   - real-deny events (target ≥3 to justify deny-promote)

4. RATIFY D-059 outcome at observation close:
   - DENY-PROMOTE if criteria met (per WP-SCP-028 §5)
   - HOLD-AT-WARN if 0 real-deny events
   - RE-SCOPE if ≥3 false positives

5. TEARDOWN session dispatch (D-057 ceremony):
   scripts/operator/scp-pattern3-dispatch.sh --teardown

Files shipped this run:
  - policies/SCP-R-009.rego
  - policies/SCP-R-010.rego
  - policies/SCP-R-011.rego
  - schemas/canonical-sdk-versions.schema.json
  - schemas/auth-contract-v1.schema.json
  - schemas/rule-config.schema.json (extended)
  - policies/scp_common.rego (extended)
  - policies/VERSIONING.md (WARN_BASELINE_RULES extended)
  - policies/rule-config.yaml (3 new opt-out keys)
  - version-manifest.json (v1.4.0)
  - tests/policies/test_SCP-R-009..R-011.json (fixtures)
  - docs/reviews/WP-SCP-028/per-rule-r1-dispositions.md
  - docs/BACKLOG.md (WP-SCP-028 → SHIPPED + roadmap rows)
  - docs/DECISIONS.md (Last Updated bump; D-059 reservation pointer)
  - STATUS.md (chain row)

3-lens R1 review outcome: ACCEPT (R-FIXPOINT MET; no REJECTs, no cure-worse).
Halt conditions encountered during run: <list, or "none">.
```

---

## §7 Halting conditions (escalate cleanly to operator)

The autonomous session HALTS with a clear operator-action message on any of:

1. **Phase 0.2 prereq miss** — `protected_primitives` block missing in CT's auth-contract-v1.yaml (the ONE hard CT prereq), OR `auth-contract-v1.yaml.sig.bundle` fails cosign-verify, OR hook not live, OR dispatch malformed/missing. (manifest_sha256 currency is NOT a prereq.)
2. **Phase 2 safety_bypass REJECT** on any of the 3 rules (auth-surface = mandatory; REJECT is hard stop)
3. **Cure-worse R2 trigger** per the per-WP scope (a fix-round introducing a worse-than-original failure mode)
4. **Context-budget split** (>8h elapsed; split-point after Phase 2 or Phase 3; carry-forward continuation prompt for next session)
5. **Fail-closed signature verification** — CT's canonical-sdk-versions.yaml.sig.bundle doesn't verify against vendored public key (rules can't ship in good faith)
6. **Test coverage <90% on any rule** AND fix-round-1 doesn't close it (signals rule-shape problem, not test problem)

---

## §8 Success criteria (re-stating §8 of plan-doc)

- 3 new Rego rules at `policies/SCP-R-009..R-011.rego`; each ≥90% opa coverage; regal lint + opa fmt clean
- 2 new JSON schemas + 1 extended schema
- VERSIONING.md WARN_BASELINE_RULES extended
- version-manifest.json bumped to v1.4.0
- BACKLOG.md WP-SCP-028 row → SHIPPED
- DECISIONS.md Last Updated bumped + D-059 reservation pointer
- STATUS.md chain row landed (triggers check-invocation-log-entry)
- 3-lens R1 review evidence at `docs/reviews/WP-SCP-028/per-rule-r1-dispositions.md`
- CI green on all required checks (policy-check / scp/policy-check + check-invocation-log-entry + r1-evidence-check)
- Operator handoff message at close
- Halt-cleanly behaviour on the named conditions
- Session dispatch teardown reminder issued

---

## §9 Inheritance from D-057 ceremony

This run is the **second genuine exercise** of the D-057 Pattern-3 + session-start dispatch ceremony (the first was the D-057 PR itself, authored from a parent-rooted session). For SCP-repo-rooted autonomous sessions like this one, the hook IS live and IS in effect; the dispatch declared in §0.2 is what allows source writes within scope.

If the autonomous session experiences ANY hook denials during the run:
- Verify the denied path is within `scope_boundary` of `.acc/active-dispatch.json` — if not, the scope was too narrow at bootstrap; HALT and ask operator to re-bootstrap with extended scope (NEVER disable the hook per D-057)
- Verify the dispatch hasn't aged past 4h TTL (`started_at` + 4h vs now) — if so, re-bootstrap
- If denied path is in scope AND TTL fresh: real bug; HALT and report

---

**Identified at:** D-058 §6 + WP-SCP-028 plan-doc §6 + §7.

**Filed:** 2026-05-29 (this prompt; concurrent with D-058 ratification PR).

**Fires when:** operator runs §0 pre-launch ceremony AND launches a Claude Code session in `~/Projects/standards-control-plane`.

**Closes when:** §6 operator-handoff message is issued AND operator runs §0.4 teardown.
