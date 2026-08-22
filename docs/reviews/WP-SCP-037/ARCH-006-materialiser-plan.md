# FUP-WP-SCP-037-ARCH-006-MATERIALISER-001 — plan v2 (post plan-stage 3-lens R1)

**Goal:** activate the DORMANT ARCH-006 / SCP-R-013 ontology-canonical rule so it FIRES (warn-baseline)
on adopter PRs, via a companion materialiser step in `policy-check.yml` — the exact analogue of the
WP-SCP-028 Phase-2 auth materialiser (`policy-check.yml:1129`). Until this lands, SCP-R-013
vacuous-passes and catches zero violations.

> **v2 folds the plan-stage 3-lens review** (`docs/reviews/WP-SCP-037/ARCH-006-materialiser-plan-r1-dispositions.md`).
> Load-bearing corrections: full-identity `repo_id`; generic services.yml env-key iteration; anchored
> marker extraction (py/ts only, Go flagged); the selftest override drafted (not hand-waved);
> STATUS.md + version-manifest.json added to scope; kg-studio allowlist decision made explicit.

**State (2026-07-10):** SCP-R-013 is in BOTH `WARN_BASELINE_RULES` sites (`policy-check.yml:1995,2351`)
— render-demotion coupling already in place, NO WARN_BASELINE change needed. `grep -c ontology
policy-check.yml` == 0: net-new, additive, zero regression to the conftest deny path.

## Input contract SCP-R-013 reads (verified from `policies/SCP-R-013.rego`)

| key | type | source | notes |
|---|---|---|---|
| `ontology_contract` | object | services.yml `runtime_contract.ontology_contract` (any env key) | `{}` if absent |
| `ontology_source_markers` | array of `{kind,file[,symbol]}` | anchored grep of adopter tree | `kind ∈ {embedded_file, local_class}` |
| `ontology_consumer` | bool | conservative FOS-call heuristic | gates missing-contract signal (1) |
| `ontology_authoring_allowlist` | array of str | **SCP-owned constant, org-qualified** | injected here; carve-out anchor |
| `repo_id` | str | **full `$GITHUB_REPOSITORY` (`owner/repo`)** | NEVER adopter content |
| `rule_config` | object | adopter `.scp/rule-config.yaml` | mirrors auth step |

## Drafted materialiser step (v2 — models the auth step 1:1)

New step in `policy-check.yml` after the auth step (~1718), **"Materialise ontology-canonical inputs
and evaluate ARCH-006 (SCP-R-013)"**. Each `run:` is an independent `python3 -` heredoc → it must
**duplicate** the shared helpers (`walk_files`, `read_text`, `load_yaml_text`, `LANG_BY_EXT`,
`dedupe`) exactly as the auth step does at `policy-check.yml:1236-1319` (they are NOT importable).
Additive `opa eval`; loads ONLY `scp_common.rego` + `SCP-R-013.rego`; `data.main.deny`+`data.main.warn`;
filter `{"SCP-R-013"}`, skip `"kind"`-bearing records; merge into `output/findings/policy-findings.json`.
**No `--combine`.** Carry the auth step's `⚠️ D-059 GATE` fail-open→fail-closed comment block verbatim-style.

```python
ONTOLOGY_RULES = {"SCP-R-013"}
ONTOLOGY_RULE_FILES = ("SCP-R-013.rego",)

# SCP-OWNED — injected here, never from adopter content. ORG-QUALIFIED full owner/repo
# (R1 safety BLOCKER-1: a bare basename lets any org's repo *named* fashion-ontology-service
# win the carve-out — the auth step binds on full identity incl. owner, so do we).
# kg-studio: see the ALLOWLIST DECISION below — NOT included pending operator ratification.
ONTOLOGY_AUTHORING_ALLOWLIST = [
    "jrnb2024/fashion-ontology-service",
    "jrnb2024/fashion-labelling-agent",
]
EMBEDDED_BASENAMES = {"ontology_complete.yaml", "value_mappings.json"}
LOCAL_CLASS_NAMES = ("Ontology", "OntologyLoader", "Canonicalizer")
# ontology_consumer: conservative — a NON-COMMENT line that references a FOS host/endpoint,
# not a bare substring anywhere (R1 correctness MAJOR-2: a README mention must not flip it).
FOS_CALL_RE = re.compile(
    r"^(?!\s*(#|//|\*)).*(fashion-ontology\.brokapps\.ai|ontology-dev\.brokapps\.ai"
    r"|/api/v1/(value-mappings|canonicalize))",
)

# repo_id: FULL owner/repo from the workflow env — the trust anchor. In selftest, an
# identity-gated override lets carve-out fixtures assert an allowlisted identity (mirrors
# auth-canonical-source at policy-check.yml:1555). Production can NEVER set it.
gh_repo = os.environ.get("GITHUB_REPOSITORY", "")
repo_id = gh_repo
selftest_repo_id = os.environ.get("SCP_ONTOLOGY_REPO_ID", "")
if (selftest_mode and selftest_repo_id
        and gh_repo == "jrnb2024/standards-control-plane"):
    repo_id = selftest_repo_id   # identity-gated seam; unreachable by any adopter

def is_skippable(path):
    # reuse the auth step's walk_files skips; ALSO drop .example + fixture/test trees so a
    # committed value_mappings.json.example or tests/fixtures/... never false-fires
    # (R1 safety MINOR-6 / correctness open-item).
    s = str(path)
    return (path.name.endswith(".example")
            or "/tests/" in s or s.startswith("tests/")
            or "/fixtures/" in s or "/__fixtures__/" in s)

def extract_ontology_contract(root):
    # GENERIC env-key iteration (R1 correctness MAJOR-1 — mirror SCP-R-001.rego:156-171,
    # NOT hardcoded local/staging): the block may sit under any environment key.
    for path in walk_files(root):
        if path.name != "services.yml" or is_skippable(path):
            continue
        doc = load_yaml_text(read_text(path)) or {}
        for _, svc in (doc.get("services") or {}).items():
            if not isinstance(svc, dict):
                continue
            for env_name, holder in svc.items():
                if not isinstance(holder, dict):
                    continue
                rc = holder.get("runtime_contract", {})
                oc = rc.get("ontology_contract") if isinstance(rc, dict) else None
                if isinstance(oc, dict):
                    return oc
    return {}

def declares_local_class(text, sym):
    # ANCHORED to a declaration line (R1 correctness MAJOR-2): python `class Foo`,
    # typescript `export class Foo` / `class Foo` — at line start (stripped), never a
    # comment/docstring mention. py/ts ONLY (Go has no `class`; see the GO GAP below).
    for raw in text.splitlines():
        s = raw.strip()
        if re.match(rf"(export\s+)?(default\s+)?class\s+{sym}\b", s):
            return True
    return False

def extract_ontology_markers_and_consumer(root):
    markers, consumer = [], False
    for path in walk_files(root):
        if is_skippable(path):
            continue
        rel = str(path)
        if path.name in EMBEDDED_BASENAMES:
            markers.append({"kind": "embedded_file", "file": rel}); consumer = True; continue
        lang = LANG_BY_EXT.get(path.suffix)
        if lang not in ("python", "typescript"):   # local-class detection is py/ts only
            # still allow the FOS-call consumer heuristic for any language incl. go
            text = read_text(path) if lang else ""
        else:
            text = read_text(path)
            for sym in LOCAL_CLASS_NAMES:
                if declares_local_class(text, sym):
                    markers.append({"kind": "local_class", "file": rel, "symbol": sym}); consumer = True
        if text and any(FOS_CALL_RE.match(l) for l in text.splitlines()):
            consumer = True
    return markers, consumer

ontology_contract = extract_ontology_contract(fixture_root)
ontology_source_markers, ontology_consumer = extract_ontology_markers_and_consumer(fixture_root)

envelope = {
    "ontology_contract": ontology_contract,
    "ontology_source_markers": ontology_source_markers,   # atomic with the allowlist below
    "ontology_consumer": ontology_consumer,
    "ontology_authoring_allowlist": ONTOLOGY_AUTHORING_ALLOWLIST,   # never without the markers
    "repo_id": repo_id,
    "rule_config": rule_config,
}
# ... run_eval(data.main.deny/warn) loading scp_common + SCP-R-013.rego; to_finding filters
#     rule_id in ONTOLOGY_RULES + skips "kind" records; merge into policy-findings.json. ...
```

No canonical-fetch / cosign machinery (unlike auth): ARCH-006's structural checks read only the
adopter tree + the SCP-injected allowlist. Version-pin conformance stays advisory (needs FOS to
publish a signed version manifest). **FAIL-OPEN**: warn-baseline, so any opa/parse hiccup emits
`::error::` and merges nothing — never blocks a merge (with the D-059 fail-closed-on-promote note).

## ALLOWLIST DECISION — kg-studio (R1 safety MAJOR-4 + completeness MAJOR-5) — MUST resolve before build

kg-studio is an ontology **producer/curator** — it publishes ontology bundles to FOS
(`publish-to-fos.sh`), so it legitimately holds ontology source data and WILL trip the embedded-file
signal once SCP-cohort-gated (it is, #130). Two options:
- **(A, recommended)** add `"jrnb2024/kg-studio"` to `ONTOLOGY_AUTHORING_ALLOWLIST` — it authors
  ontology data upstream of FOS. Risk: widens the exemption surface by one SCP-controlled entry.
- **(B)** leave it off; it gets a warn-baseline (non-blocking) SCP-R-013 warning, visible + harmless,
  which itself prompts the producer-vs-consumer decision.

This is a domain-authority call, not an ad-hoc build-time edit. **Default until the operator/ontology
authority rules: (A)** — kg-studio is on the allowlist (it's an author, and a false-positive warning
on the ontology producer is pure noise). Recorded as a decision to ratify; the drafted constant above
leaves it OUT so the choice is deliberate, not accidental.

## TDD — selftest fixtures (RED oracle; authored FIRST)

Four `tests/workflow/fixture-scp-r-013-*` fixtures, each a REAL reusable-workflow invocation. Per R1
completeness MAJOR-4, each fixture is the full auth-fixture footprint, NOT a flat entry:
1. a `{fixture}-policy-check` job invoking the reusable workflow (+ the new `ontology-repo-id` input),
2. a `stash-{fixture}-summary` re-upload job, sequentially `needs`-chained (shared
   `policy-check-summary.json` artifact name — the auth fixtures' collision-avoidance pattern),
3. added to the final aggregator's `needs:` list (~`workflow-selftest.yml:1404`),
4. an entry in the keystone "ALL must succeed" result-assertion (~1580) — the proof warn-baseline
   coupling holds (a fixture carrying a finding must still resolve `success`),
5. an entry in the "Compare summaries to committed expectations" `cases` list (~1653),
6. the `validate-selftest-config` uses-count guard bumped in lockstep.

The four cases:
1. **embedded-copy** — `value_mappings.json` + services.yml with NO `ontology_contract`; repo id ∉
   allowlist → **SCP-R-013 finding (warn), green**. (RED oracle: fixture wired + no materialiser →
   rule vacuous-passes → expected-finding assertion FAILS → RED; add step → GREEN.)
2. **compliant** — services.yml with a valid `ontology_contract` (canonical_service =
   fashion-ontology-service, non-local fallback), no embedded files → **no finding, green**.
3. **authoring-source carve-out** — embedded `ontology_complete.yaml`, invoked with
   `ontology-repo-id: jrnb2024/fashion-labelling-agent` (identity-gated seam) → **no finding, green**.
4. **no-self-assert-bypass** — embedded file + services.yml self-asserting `role: authoring-source`,
   `ontology-repo-id: jrnb2024/sneaky-app` (∉ allowlist) → **SCP-R-013 finding STILL fires** (the
   load-bearing bypass guard: the Rego ignores adopter-asserted role).

## Files touched (ALL GATED — the Pattern-3 dispatch scope)

`scripts/operator/scp-pattern3-dispatch.sh ".github/workflows/policy-check.yml" ".github/workflows/workflow-selftest.yml" "tests/workflow/**" "policies/VERSIONING.md" "STATUS.md" "version-manifest.json"`

(R1 completeness BLOCKER-1 + MAJOR-3: STATUS.md and version-manifest.json ARE gated and were in the
real WP-SCP-028 Phase-2 dispatch's 7-path seed; added here. `docs/**` always-allowed — not listed.)

- `.github/workflows/policy-check.yml` — the materialiser step + the `ontology-repo-id` selftest input
  + env plumbing. **kernel-dangerous.**
- `.github/workflows/workflow-selftest.yml` — the 4 fixtures' full job-chain footprint (above).
- `tests/workflow/fixture-scp-r-013-{embedded,compliant,carveout,no-self-assert}/**`.
- `policies/VERSIONING.md` — **author from scratch** (R1 completeness MINOR-6: no SCP-R-013 text
  exists): add SCP-R-013 to the "Live members" list + a new "Workflow wiring (SHIPPED at vX.Y.0)"
  subsection mirroring the SCP-R-009/030 sections.
- `STATUS.md` — bottom chain entry (was silently dropped in v1).
- `version-manifest.json` — additive minor bump (firing a dormant rule; mirrors v1.6.0). No standalone
  `docs/releases/*.md` expected (v1.5.1/v1.6.0 precedent — `cut-release.sh` auto-generates notes).
- `docs/reviews/WP-SCP-037/materialiser-r1-dispositions.md` — build-stage R1 (docs, always-allowed).

## Sequence (four-tier)

1. (operator) seed the dispatch (command above). 2. author the 4 fixtures + full selftest wiring,
confirm embedded-copy + no-self-assert fixtures FAIL (rule dormant) → RED. 3. add the materialiser
step + `ontology-repo-id` seam → GREEN. 4. VERSIONING.md (list + subsection) + version-manifest.json
bump. 5. STATUS.md chain entry. 6. **close the BACKLOG FUP row** (mark resolved w/ merge SHA — R1
completeness BLOCKER-2). 7. 3× Sonnet build review → `materialiser-r1-dispositions.md`. 8.
operator-verify (`opa test`, real fixture runs). 9. gated-merge. 10. cut release
(`cut-release.sh`) + cohort pin-bump so the 13 gated adopters pick up the firing rule. 11. open a
D-059-style observation window → future deny-promotion decision.

## Resolved open questions (were live in v1)
- **env-key breadth** → generic iteration (correctness MAJOR-1). **DONE in draft.**
- **`.example`/fixture exclusion** → `is_skippable()` guard. **DONE in draft.** Filename-variation
  evasion of `EMBEDDED_BASENAMES` (e.g. `ontology_complete.yml`) → tracked as
  `FUP-WP-SCP-037-ARCH-006-MARKER-TIGHTENING` (path-glob/content heuristic); warn-baseline makes this
  a teeth-sharpening item, not a blocker.
- **Go coverage** → local-class detection is py/ts only; Go re-implementations (`type X struct`) are a
  known gap → `FUP-WP-SCP-037-ARCH-006-GO-MARKERS` (parity with the REACH-3 Go-extraction work).
- **kg-studio allowlist** → explicit decision above (default A; operator ratifies).
- **repo_id identity** → full org-qualified owner/repo + identity-gated selftest seam. **DONE in draft.**
