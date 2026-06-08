# RULE-006 — destructive schema-migration operations must carry the `scp:protected-table-attested` marker

**Status:** DRAFT
**Author:** @jrnb2024
**Filed:** 2026-06-08
**Target release:** v2.0.0 (SCP federation primitive — first MAJOR; the deny-promotion / born-at-deny release).
**Type:** rule-add
**Quorum required:** 1 (single-operator mode per D-031)
**Review window:** 48h wall-clock CEILING per D-040 (early-merge permitted in single-operator mode when CI green + 3-lens R1 fixpoint).
**Bypass-surface non-empty:** `false` *(no new `.scp/rule-config.yaml` key; reuses existing per-finding waiver-suppression via `data.waivers` and existing `.scp/rule-config.yaml disable: true`. The attestation marker is a closed convention in the Rego, not a configurable adopter-side bypass.)*

---

## 1. Summary

Catches the **destructive-migration-without-review** pattern: an Alembic-style migration that drops a table/column, drops a constraint, renames a table, or alters a column — i.e. an operation that can silently rewrite or destroy an auth / identity / tenancy ("protected") table — must carry the standalone comment marker `# scp:protected-table-attested`. The marker is the author's explicit attestation that the migration was checked against the domain's protected-tables policy. **Ships at `deny` baseline (born-at-deny)** — it is a self-contained, high-precision, cheap-to-satisfy gate on a genuinely dangerous class, filed under WP-SCP-025 Phase 2 / D-053. Mirrors SCP-R-003 (vendoring-attestation marker) exactly in shape.

## 2. Motivation

- **Concrete failure pattern:** a destructive migration (`op.drop_column`, `op.alter_column` with a type change, raw `op.execute("DROP …")`) on a protected table (`users`, `permission_schemas`, `oauth_clients`, `tenants`, …) sails through review because the diff *looks* routine and the reviewer doesn't connect the table name to its protected status. The data loss / auth breakage is discovered post-deploy.
- **Threat model:** schema migrations are uniquely dangerous — they run with elevated DB privilege at deploy time, are hard to reverse once data is dropped, and an AI-assisted migration generator will happily emit a destructive `alter_column` to satisfy a model change. The gate forces a human to *pause and assert* before a destructive migration can merge.
- **Why a marker, not a table-list match:** per **D-058 LINKAGE-not-VALUES**, SCP must not author or carry the protected-table list — CT (the data/identity authority) owns it. A self-contained rule cannot read CT's `PROTECTED_TABLES` constant at evaluation time without a cross-repo state read (the exact reason the original "protected_tables_updated_with_migration" candidate was deferred to Phase 2 in WP-SCP-025 §3.3). The marker resolves this: SCP gates the **dangerous operation class** (destructive DDL) and the author supplies the **conformance assertion** (the marker = "I checked this against the protected-tables policy"). SCP gates linkage; the domain owns values.

## 3. Rule specification

### 3.1 Match conditions

Fires per-file against any file that is an **Alembic-style migration** — basename ends `.py` AND the path contains a `versions/` segment (`(^|/)versions/`, the Alembic revision-script convention) — AND whose content performs at least one **destructive / structural DDL operation**:

```
op.drop_table(            op.drop_column(           op.drop_constraint(
op.alter_column(          op.rename_table(
op.execute("… DROP|ALTER|TRUNCATE …")   # raw-SQL escape hatch, case-insensitive
```

…UNLESS the content carries the standalone marker line:

```
# scp:protected-table-attested
```

(`//` accepted for parity though migrations are Python.)

**Additive operations are intentionally NOT matched** (`op.create_table`, `op.add_column`, `op.create_index`, `op.bulk_insert`) — a purely-additive migration is not the dangerous class and must pass without a marker (FP-surface control, §4).

### 3.2 Severity & threshold

- **Initial threshold:** `deny` — born-at-deny. Justification: the rule is self-contained (no external manifest, no signing dependency), high-precision (it matches concrete `op.<destructive>(` tokens, not heuristics), and trivially satisfiable (one comment line). There is no FP-driven reason to ramp through warn first, and the operator directive (2026-06-07 operating mode) is "verify it works, then promote — skip the observation window."
- **NOT a member of `WARN_BASELINE_RULES`.** Unlike SCP-R-004/R-030, SCP-R-012's `deny` is a real merge-gate block.
- **Adopter override:** existing `.scp/rule-config.yaml disable: true` suppresses; per-finding waiver per the existing SCP-R-NNN pattern (a waiver is the right tool when a destructive op is reviewed-and-intended on a non-protected table and the author prefers a waiver to the inline marker).

### 3.3 Annotation contract

- **Rule-specific annotation:** `::error file=<migration-path>,title=SCP-R-012::<path> performs a destructive schema-migration operation but does not declare the scp:protected-table-attested marker …`
- Reuses the standard structured deny payload (`rule_id` / `file` / `message` / `remediation_url` / `msg`) — no new SCP-EXXX error code claimed.

### 3.4 Implementation

Per-file via `input.source_file` + `input.content` (the SCP-R-003 envelope). Full implementation at `policies/SCP-R-012.rego`. Shape mirrors SCP-R-003: rule-local `scp_r_012_*` helpers; potential denies factored into `scp_r_012_raw_findings`; public `deny` filtered by `scp_active_waiver_for` + `scp_rule_config_disabled`; two `warn` observability records for waiver / rule-config suppression. Reuses ONLY the estate-wide suppression helpers from `scp_common.rego`.

Detection key predicates:

```rego
scp_r_012_is_migration_file(path) if {
    endswith(path, ".py")
    regex.match(`(^|/)versions/`, path)
}

scp_r_012_has_destructive_op(content) if {
    some pattern in scp_r_012_destructive_patterns
    regex.match(pattern, content)
}

scp_r_012_has_attestation_marker(content) if {
    regex.match(`(?m)^\s*(#|//)\s*scp:protected-table-attested\s*$`, content)
}
```

(RE2 — no backreferences; `(?i)` / `(?m)` inline flags only.)

## 4. False-positive surface

- **Additive-only migrations** (`create_table` / `add_column` / `create_index`): do NOT match — no destructive pattern fires. This is the dominant migration shape, so the rule is silent on most migrations.
- **`op.alter_column` for a benign nullability/comment change:** matches (alter is in the destructive set) → requires the marker even when the alter is safe. This is intentional over-inclusion: type/nullability changes on a protected table ARE destructive, and distinguishing safe-alter from unsafe-alter would require parsing the alter arguments (out of scope for a marker gate). Cost to satisfy is one comment line; alternatively the author files a waiver. Estimated this is the main FP source; acceptable given the trivial remediation.
- **A migration outside a `versions/` directory** (non-Alembic layout): not matched. If a cohort adopter uses a non-`versions/` migration convention, the rule is silent there — tracked-forward `FUP-RULE-006-MIGRATION-PATH-CONVENTIONS` (extend the path predicate per observed adopter layouts) rather than guessed-at now.
- **`source_file` / `content` absent:** defensive `object.get` defaults → short-circuit to no finding (the SCP-R-003 safe-failure mode).

Aggregate: the rule fires only on destructive DDL inside a recognised migration file without a marker — a narrow, intentional target. The over-inclusion is bounded to "destructive op present" and remediated by one line.

## 5. Bypass surface

No new policy-engine bypass surface. The marker is a closed convention in the Rego (`scp:protected-table-attested`); it is the *intended* satisfaction path, not a bypass — an author who adds it without checking is making a false attestation (a review/trust failure, not a control failure, identical in kind to SCP-R-003's vendoring-attested marker). Suppression remains the existing waiver + `disable` paths, both observable via the emitted `warn` records and (for waivers) bounded by SCP-R-007's ≤90-day expiry.

## 6. Test fixtures

Per `policies/tests/scp_r_012_test.rego` (inline `_test.rego`, the current convention since SCP-R-007; no `testdata/` dir):

| # | Fixture | Expected | Tests |
|---|---|---|---|
| 1 | `versions/…drop.py` + `op.drop_table` + marker | no findings | marker satisfies |
| 2 | `versions/…add.py` + `create_table`/`add_column`, no marker | no findings | additive-only not matched |
| 3 | `app/models/user.py` + `op.drop_table`, no marker | no findings | non-migration path |
| 4 | `versions/notes.md` + drop text | no findings | non-`.py` |
| 5 | `versions/…raw.py` + `op.execute("DROP …")` + marker | no findings | raw-SQL + marker |
| 6 | `versions/…drop.py` + `op.drop_table`, no marker | 1 deny | drop_table |
| 7 | `versions/…dropcol.py` + `op.drop_column`, no marker | 1 deny | drop_column |
| 8 | `versions/…alter.py` + `op.alter_column`, no marker | 1 deny | alter_column |
| 9 | `versions/…rawalter.py` + `op.execute("alter table …")`, no marker | 1 deny | raw-SQL alter (case-insensitive) |
| 10 | destructive + active waiver | no findings + `kind=waiver` warn | waiver suppression |
| 11 | destructive + expired waiver | 1 deny + no warn | fail-closed expiry |
| 12 | destructive + rule-config disable | no findings + `kind=rule_config` warn | rule-config suppression |
| 13 | destructive + waiver missing `expires_at` | 1 deny + no warn | fail-closed missing-expiry |

Per-rule OPA coverage: **100%** on `SCP-R-012.rego` (97.5% aggregate incl. touched `scp_common` helpers), `--threshold 90 --fail-on-empty` green.

## 7. Promotion / observation path

N/A — born-at-deny. There is no warn→deny ramp; the rule ships deny in v2.0.0 under D-053. Reversibility is preserved per VERSIONING.md invariant 6 (any adopter flips it off via `.scp/rule-config.yaml` in ≤24h Renovate cycle), so a noisy-in-practice outcome does not require an SCP rollback. If real-world FP rate proves higher than §4 estimates, the response is per-adopter `disable` + a follow-up RFC narrowing the `alter_column` match — not a v2.0.x revert.

## 8. Open questions

- **Migration path conventions beyond `versions/`** — deferred to `FUP-RULE-006-MIGRATION-PATH-CONVENTIONS`; v2.0.0 ships the Alembic `versions/` convention only (covers PIM + CT, the migration-bearing cohort adopters).
- **`alter_column` granularity** — v2.0.0 treats all `alter_column` as destructive-class. A future refinement could exempt pure comment/default-only alters; not worth the parsing complexity at born-at-deny given the one-line remediation.
