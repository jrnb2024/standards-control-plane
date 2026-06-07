# SCP-R-010 import-fence — static-extractor evasion surface

**FUP:** FUP-WP-SCP-028-IMPORT-FENCE-EVASION-DOC-001
**Status:** documented (this file) — closes the FUP's "record what is NOT caught"
obligation so D-059 does not assume the extractor is exhaustive.
**Authored:** 2026-06-07 (WP-SCP-028 Phase 2 companion materialisation PR).

## Why this exists

SCP-R-009/010/011 read `input.adopter_*` arrays that the policy-check workflow's
auth-canonical materialisation step extracts from the adopter's checked-out tree
(`.github/workflows/policy-check.yml` → "Materialise auth-canonical inputs and
evaluate auth rules"). Rego cannot AST-parse source, so the extractor is a
**line-oriented heuristic**, deliberately CONSERVATIVE: it prefers
false-negatives (a missed shadow) over false-positives (a spurious finding),
because at warn-baseline a missed finding is observability debt while a spurious
one is adopter friction. The set of things it does NOT catch is recorded here so
the D-059 deny-promotion decision is made with eyes open — a deny-promotion that
assumed exhaustiveness would be unsound.

## What the extractor DOES catch (SCP-R-010 `adopter_source_files`)

For each `.py` / `.ts` / `.tsx` / `.go` file under the adopter root (vendor /
build / VCS dirs skipped):
- `imports_ct_auth`: an `import`/`from`/`require(`/quoted-go-import line that
  contains a ct-auth marker (`ct_auth`, `ct-auth`, `control-tower-auth`,
  `@control-tower/auth`, `control_tower_auth`).
- `declared_symbols`: top-level `def`/`class` (python), `export`/`function`/
  `class`/`const` (typescript), `func`/`type` (go) names.
- `reexported_symbols`: TS `export { … }` lists and python `__all__` entries.
A declared/re-exported symbol that matches a `protected_primitives.tier_deny`
(deny-class) or `tier_warn` (warn-class) name for the file's language fires.

## What the extractor does NOT catch (the evasion surface)

These are LINKAGE-faithful gaps — a determined adopter (or an honest one with an
unusual style) can shadow a protected primitive without the extractor seeing it:

1. **Dynamic / aliased binding.** `validate_token = getattr(mod, "x")`,
   `vt = validate_token; def vt(...)`, `globals()["validate_token"] = …`,
   `setattr(self, "validate_token", …)` — the name never appears on a `def`/
   `class`/`export` line, so it is not in `declared_symbols`.
2. **Case / separator variants.** The match is exact against the canonical
   symbol spelling. `Validate_Token`, `validateToken` in a `.py`, `validate__token`
   are not matched. (The canonical sets are the authority on spelling; a rename is
   a different symbol and arguably not a shadow — but an intentional near-miss
   evades.)
3. **Indirect re-export / barrel files.** `export * from './shim'`,
   `from .shim import *`, Go dot-imports (`import . "shim"`) re-expose a shadow
   without naming it; only explicit `export { … }` / `__all__` lists are read.
4. **Conditional / lazy / runtime import.** `if TYPE_CHECKING:`-guarded imports,
   imports inside a function body, `importlib.import_module("ct_auth")`,
   `require()` computed at runtime — `imports_ct_auth` may be False, so the file
   is not even considered an importing file and the fence does not apply.
5. **Method-level / nested declarations.** A protected name declared as a class
   method or a closure (`class X: def validate_token(self): …`) is detected by the
   `def` scan, but a name bound only as a lambda or assigned attribute is not.
6. **Non-{py,ts,go} languages.** Files outside `.py`/`.ts`/`.tsx`/`.go` are not
   scanned (no language mapping); a shadow in another language is invisible.
7. **Whole-file false-negative on read failure.** A file that cannot be decoded
   as UTF-8 is skipped (returns `""`), so a shadow in a mis-encoded file is missed.

## Related extractor gaps (SCP-R-009 / SCP-R-011)

- **SCP-R-009 package-name normalization.** `adopter_ct_auth_deps` maps a fixed
  alias table (e.g. npm `control-tower-auth` → canonical key `ct-auth-ts`). A dep
  declared under an unlisted alias, a monorepo workspace path, a git/URL/path
  dependency, or a non-`X.Y.Z` version spec (range/caret only, SHA pin) is not
  mapped → no version comparison. SHA-pin detection is separately tracked as
  `FUP-WP-SCP-028-SHA-PIN-DETECT-001`.
- **SCP-R-011 claim-shape + issuer detection** is marker/heuristic-based:
  `handles_authorization` keys on the literal `Authorization`/`Bearer ` tokens;
  `declared_claim_shape_version` / `claims_uses_old_shape` key on explicit
  markers; `hardcoded_issuers` only captures URL-shaped or `control-tower`-shaped
  quoted values on a line mentioning `iss`/`issuer`. Type-aware old-shape
  detection and non-marker claim-shape inference are out of scope (the
  `_legacy`/`_internal` suffix heuristic is `FUP-WP-SCP-028-LEGACY-SUFFIX-WARN-001`).

## Consequence for D-059

The extractor is a **trip-wire for the honest-mistake and casual case**, not an
adversarial control. Because all three rules ship warn-baseline (never block),
the gaps above are observability debt, not a security hole, in Phase 2. A D-059
**deny-promotion** for SCP-R-010 (or 009/011) MUST weigh these gaps: promoting a
rule to blocking on a heuristic that an adopter can trivially evade would create
a false sense of enforcement. Options at D-059 include: (a) hold at warn; (b)
deny-promote only the unambiguous sub-conditions (e.g. fail-closed signature,
exact tier_deny shadow) while keeping the heuristic ones at warn; (c) invest in
AST-grade extraction before promoting. This file is the input to that decision.
