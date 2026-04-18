# WP-SCP-019 Review Findings

Stub. Populated as slices 019A–019F land.

## Slice 019A — adversarial review (2026-04-18)

Three parallel reviewer agents (rule/schema correctness, estate reality,
repo wiring) surfaced a combined defect list before the 019A commit.
Findings grouped by disposition:

**Fixed in 019A before commit**

- `interpreter: none` exemption dropped (too loose; SVC-001 permits Go mesh
  services to declare `interpreter: none` for real networked services).
- Contradiction between "must include" rule text and optional schema
  resolved by clarifying that presence is evaluator-enforced, not
  schema-enforced (consistent with SVC-001's pattern).
- Signals split into static (auto-checked) and runtime (out of scope for
  static evaluator) — matches SVC-002's existing shape.
- `accepted_modes` gained `uniqueItems: true`; duplicate-by-mode-id check
  deferred to evaluator semantics and added as an explicit signal.
- `audience` pattern pinned to bare app-id (`^[a-z][a-z0-9-]*$`); rule text
  clarifies it is not a URI.
- `waiver_ref` definition tied to `output/findings/waivers.json`.
- Multi-mode example added (SCP itself declares `[user_oidc, bearer_legacy]`).
- Exempt-path list added covering OIDC bootstrap paths (`/auth/*`,
  `/api/auth/*`, `/.well-known/*`, `/health`, `/status-app/health`).
- `key_id_prefix` added as optional metadata for `mode.api_key` to give the
  evaluator something to cross-reference against.
- Schema `$ref` style aligned to `./<name>.schema.json` convention.
- Programme plan gained explicit Programme Protocol Position, External
  Dependencies (CT agent-key issuer registration, SDK vendoring), and Risks
  sections.
- Freeze directive path reference added to the programme plan.
- Architecture doc clarified that static file scanning includes code-pattern
  scans, not just schema validation.
- BACKLOG.md gained Phase 7 / SCP-071 row.
- Review-pack stub created under `docs/reviews/WP-SCP-019/`.

**Deferred to later slices (by design, not dodge)**

- README.md programme-complete banner updated in 019F alongside STATUS.md,
  per the user's explicit slice plan (019F is the publish slice).
- `key_id_prefix` semantics and `issuer` enum tightening left to 019B/019E
  once the CT agent-key registration conversation lands.
- Cross-repo SDK-vendoring evidence path operationalised in 019F.

**Rejected / OPINION-only**

- Schema `$id` injection: repo convention is loader-injected (`schema_tools._load_schema_file`). Adding `$id` to this schema alone would diverge from 14 sibling schemas. Revisit only if the loader changes.
- Commit-SHA-only rule reference: kept, paired with file-path reference to
  `src/standards_control_plane/service.py`. SHA serves as an archaeological
  marker; file-path ref survives history edits.
