# RULE-005 — credential-pattern values must not appear in committed `.env*` files (except `.env.example` / `.env.template` / `.env.dist`)

**Status:** DRAFT
**Author:** @jrnb2024
**Filed:** 2026-05-25
**Target release:** v1.3.0 (SCP federation primitive).
**Type:** rule-add
**Quorum required:** 1 (single-operator mode per D-031)
**Review window:** 48h wall-clock CEILING per D-040 (early-merge permitted in single-operator mode when CI green + 3-lens R1 fixpoint).
**Bypass-surface non-empty:** `false` *(no new `.scp/rule-config.yaml` key; reuses existing waiver-suppression via `data.waivers` for rule SCP-R-008 and existing `.scp/rule-config.yaml disable: true` for SCP-R-008. The exemption-by-filename mechanism is a closed allow-list defined in the Rego itself, not a configurable adopter-side bypass.)*

---

## 1. Summary

Catches the standard secret-leakage pattern: a committed `.env`-class file (not the template variants) contains values that look like credentials (high-entropy strings, JWT/API-key shapes, common cloud-credential prefixes). Ships at **warn** baseline given the heuristic nature; promotion to deny is a v1.4.0+ separate RFC after ≥4 weeks of low-FP observation across the cohort.

## 2. Motivation

- **Concrete finding:** multiple near-misses across the estate where `.env.production` or `.env.docker` files have been staged with real credential values (caught at review time, not by automation). Standard secret-leakage attack vector — every Web-discoverable credential leak in the last 18 months has had a "committed env file" antecedent.
- **Threat model:** GitHub repo public/private boundary is one config-flip away; a private repo with committed credentials becomes a public repo with committed credentials at any moment. AI-assisted code-author tools may auto-create `.env` files with sample-but-credential-shaped values and the author may not realise the file is committed. The rule catches at gate time.
- **Prior conversation:** WP-SCP-025 §3 candidate list 2026-05-09; selected at Phase 1 kickoff 2026-05-25 per WP-SCP-025 v1.0 §3.2.

## 3. Rule specification

### 3.1 Match conditions

Fires per-file against any file whose name matches `^\.env(\..+)?$` (regex anchored to filename basename) EXCEPT when the basename matches the closed exemption set:

```
EXEMPT_BASENAMES = {".env.example", ".env.template", ".env.dist", ".env.sample"}
```

For non-exempt `.env*` files, parses line-by-line looking for `KEY=VALUE` patterns where `VALUE` matches ANY of:

1. **Generic credential prefixes** (case-insensitive): `^(sk_|pk_|api_|key_|token_|secret_|password_|pwd_)`. These prefixes are widely used in commercial-API conventions.
2. **JWT shape:** `^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$` (3 base64url segments joined with `.`).
3. **AWS-style access key:** `^AKIA[A-Z0-9]{16}$` (20 chars).
4. **Stripe-style live key:** `^sk_live_[A-Za-z0-9]{24,}$`.
5. **High-entropy generic:** value length ≥32 AND has ≥4 distinct character classes (upper / lower / digit / symbol) AND no whitespace AND no English-dictionary-word substring (we use a conservative dictionary subset — see §3.4).

Lines matching `^\s*#` (comments) are skipped. Lines matching `KEY=` with empty / placeholder values (`KEY=`, `KEY=changeme`, `KEY=your-key-here`, `KEY=<placeholder>`, `KEY=xxxx`) are skipped.

### 3.2 Severity & threshold

- **Initial threshold:** `warn` — MEDIUM false-positive risk per the heuristic nature of patterns 4 + 5. Adopters see `::warning::` annotations rather than merge-blocking deny.
- **Promotion path:** to `deny` after ≥4 weeks of cohort observation with FP rate ≤2%. Separate RFC at v1.4.0+ minimum.
- **Adopter override:** existing `.scp/rule-config.yaml disable: true` continues to suppress. Per-finding waiver per existing SCP-R-NNN pattern.

### 3.3 Annotation contract

- **Infrastructure error code:** reuses `SCP-E004` (warn) per ADOPT-001 §12.7.7 — no new SCP-EXXX code claimed.
- **Rule-specific annotation:** `::warning file=<.env-path>,title=SCP-R-008,line=%d::credential-pattern value detected: KEY=%s VALUE=<truncated 8 chars>...` (intentionally truncates VALUE to 8 chars to avoid splashing the actual secret in CI logs).
- **Sibling commit-status text:** `N SCP-R-008 finding(s) (warn)` (~30 chars budget).

### 3.4 Implementation sketch

Per-file via `input.path` matching and content scanning:

```rego
package main

import rego.v1

scp_r_008_rule_id := "SCP-R-008"
scp_r_008_remediation_url := concat("", [...])

scp_r_008_exempt_basenames := {
  ".env.example", ".env.template", ".env.dist", ".env.sample"
}

scp_r_008_env_file_pattern := `^\.env(\..+)?$`

scp_r_008_credential_patterns := [
  `^(?i)(sk_|pk_|api_|key_|token_|secret_|password_|pwd_)`,
  `^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$`,
  `^AKIA[A-Z0-9]{16}$`,
  `^sk_live_[A-Za-z0-9]{24,}$`,
]

scp_r_008_placeholder_values := {
  "", "changeme", "your-key-here", "<placeholder>", "xxxx",
  "PLACEHOLDER", "TODO", "TBD",
}

scp_r_008_is_env_file(path) if {
  basename := scp_r_008_basename(path)
  regex.match(scp_r_008_env_file_pattern, basename)
  not basename in scp_r_008_exempt_basenames
}

scp_r_008_basename(path) := basename if {
  parts := split(path, "/")
  basename := parts[count(parts) - 1]
}

# Per-line credential-pattern check
scp_r_008_raw_findings contains finding if {
  some path, content in input.files  # convention: file map
  scp_r_008_is_env_file(path)
  lines := split(content, "\n")
  some line_idx
  line := lines[line_idx]
  not startswith(trim_space(line), "#")
  contains(line, "=")
  parts := split(line, "=")
  count(parts) >= 2
  key := trim_space(parts[0])
  value := trim_space(concat("=", array.slice(parts, 1, count(parts))))
  not value in scp_r_008_placeholder_values
  scp_r_008_value_looks_like_credential(value)
  finding := {
    "message": sprintf("SCP-R-008 credential-pattern value in %s line %d: KEY=%s VALUE=<truncated>%s...",
                       [path, line_idx + 1, key, substring(value, 0, 8)]),
    "rule_id": scp_r_008_rule_id,
    "file": path,
    "line": line_idx + 1,
    "remediation_url": scp_r_008_remediation_url,
  }
}

scp_r_008_value_looks_like_credential(value) if {
  some pattern in scp_r_008_credential_patterns
  regex.match(pattern, value)
}

# Public deny (the workflow's WARN_BASELINE_RULES set demotes to warn annotations)
deny contains output if {
  some finding in scp_r_008_raw_findings
  not scp_active_waiver_for(scp_r_008_rule_id)
  not scp_rule_config_disabled(scp_r_008_rule_id)
  output := object.union(finding, {"msg": finding.message})
}
```

**Note on `input.files` convention:** SCP-R-001/002/003/004 evaluate against a single `input` per file (conftest invokes Rego per-file). SCP-R-008 needs filename + content correlation per finding. The current conftest envelope already passes filename via the `input.source_file` field (used by SCP-R-003 — see `policies/SCP-R-003.rego` for the precedent). SCP-R-008 reuses this — see §3.4 above where the implementation reads `source_file := object.get(input, "source_file", "")` and `content := object.get(input, "content", "")`, matching SCP-R-003's per-file shape exactly (NOT the multi-file `input.files` map sketched here; the §3.4 PoC was illustrative — actual implementation uses SCP-R-003's per-file `source_file` + `content` convention).

Conservative entropy check (pattern 5) is **DEFERRED to v1.4.0** — the first-ship corpus uses patterns 1-4 only (prefix-based + shape-based; explicitly enumerable). Pattern 5 (entropy + dictionary subtract) introduces a non-trivial dictionary-bundling concern; deferring removes that risk for v1.3.0 and we observe pattern 1-4 FP rate first. **This deferral is locked in §3.1 above** — the live rule shipped in this slice does NOT include pattern 5.

Reuses `scp_common.rego` helpers: `scp_active_waiver_for(rule_id)` + `scp_rule_config_disabled(rule_id)`.

### 3.5 WARN_BASELINE_RULES set update

`.github/workflows/policy-check.yml` carries `WARN_BASELINE_RULES = {"SCP-R-004"}` (hardcoded set per WP-SCP-022 020P). This slice extends to `{"SCP-R-004", "SCP-R-008"}` (1-line edit + mirror in conftest test corpus + `tests/conflict_gate/` parity). TF-020P-001 (data-driven `policies/rule-baselines.yaml`) still applies as the proper closure path when a 3rd warn-baseline rule lands.

## 4. False-positive surface

- **Sample-but-credential-shaped values** in `.env` (NOT in the exemption list): an adopter using `.env.local` with a real-looking-but-fake value for testing. Recommended response: rename to `.env.example` / `.env.local.example`, OR file an adopter `.scp/rule-config.yaml disable`. Estimated FP rate: ≤1% (most adopters use the convention names).
- **Stripe-test-key values** (`sk_test_…` starting with `sk_test_`) — these match pattern 1 (`sk_` prefix) but are by-design not credentials. Stripe test keys ARE secret-ish (rate-limited; should not be public), so the warn is arguably correct here; we leave as-is for v1.3.0 and observe.
- **JWT shape in unrelated values:** an `.env` with a legitimate JWT field for testing. Same as above — warn is arguably correct.
- **`source_file` field absent:** if a future conftest invocation omits `source_file`, the rule short-circuits to no finding (defensive `object.get` default). This is the safe failure mode.

Aggregate expected FP rate (across patterns 1-4 only, given pattern 5 deferred): ≤1.5%. Threshold for promotion-to-deny: FP rate ≤2% over ≥4 calendar weeks of cohort observation.

## 5. Bypass surface

No new bypass surface in the policy-engine sense. The closed exemption-by-filename set (`.env.example` / `.env.template` / `.env.dist` / `.env.sample`) is a constant in the Rego; adding new exemption names requires a separate rule-RFC. The closed-list design is INTENTIONALLY less flexible than `.scp/rule-config.yaml` so adopters can't accidentally exempt their actual `.env.production`.

## 6. Test fixtures

### 6.1 Conftest test matrix

Per `tests/policies/SCP-R-008/`:

| # | Fixture | Expected verdict | Tests |
|---|---|---|---|
| 1 | `.env.example` with `API_KEY=sk_test_abc123…` | no findings | exemption-by-filename |
| 2 | `.env.template` with credential-pattern values | no findings | exemption-by-filename |
| 3 | `.env.dist` with credential-pattern values | no findings | exemption-by-filename |
| 4 | `.env` with `API_KEY=changeme` | no findings | placeholder-skip |
| 5 | `.env` with `# API_KEY=sk_live_…` (commented) | no findings | comment-skip |
| 6 | `.env` with `API_KEY=sk_live_<TESTKEY-24+-CHARS>` | 1 deny finding (warn at runtime) | pattern 4 hit |
| 7 | `.env` with `JWT=eyJhbGciOiJI…` (3-segment shape) | 1 finding | pattern 2 hit |
| 8 | `.env` with `AWS_KEY=AKIAIOSFODNN7EXAMPLE` | 1 finding | pattern 3 hit |
| 9 | `.env` with `PASSWORD_RESET_TOKEN=longvalue…` | 1 finding | pattern 1 hit |
| 10 | `.env.local` with credential-pattern values | 1 finding | non-exempt suffix |
| 11 | `.env.production` with credential-pattern values | 1 finding | non-exempt suffix |
| 12 | `.env` with rule-config disable for SCP-R-008 | no findings | rule-config suppression |
| 13 | `.env` with active waiver for SCP-R-008 | no findings + warn record | waiver suppression |
| 14 | non-`.env` file (e.g., `config.yml`) with credential-pattern values | no findings | path-scoping |
| 15 | empty `.env` | no findings | edge case |

### 6.2 Per-rule OPA coverage

Target ≥90% per `scripts/scp-pre-push-verify.sh` parity with CI.

## 7. Bake observation + promotion path

- v1.3.0 cut → PIM Renovate auto-PR → ≥1 calendar week observation per WP-SCP-024 invariant 8.
- Warn observation for ≥4 calendar weeks before promotion-to-deny RFC opens.
- Promotion-to-deny RFC blocked if FP rate > 2% OR if PIM (or any future cohort adopter) files a TF asking for the rule to be reverted.

## 8. Open questions

None at filing time — operator-attended ratification 2026-05-25 locked all decision points. Pattern 5 (entropy + dictionary-subtract) DEFERRED to v1.4.0+ separate RFC.
