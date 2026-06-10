# RULE: SCP-R-008 — see docs/reviews/rule-proposals/RULE-005-secrets-not-in-committed-env-files.md
#
# Credential-pattern values must not appear in committed `.env*` files
# (except `.env.example` / `.env.template` / `.env.dist` / `.env.sample`).
# Ships at warn baseline. NOTE (v2.0.0 / amended D-053): this rule was
# plumbing-dormant from v1.3.0 to v2.0.0 — the evaluation feed never
# delivered .env content until the rule input contract
# (policies/rule-inputs.yaml) landed. v2.0.0 is the release that first
# makes it FIRE; promotion to deny is a separate decision taken on
# observed real-traffic precision (fires correctly, zero FPs on live
# cohort PRs), not on a calendar window. Filed via WP-SCP-025 Phase 1
# (operator-authorised early kickoff 2026-05-25).
#
# Defines its OWN `scp_r_008_*` predicates per the SCP-R-004
# SAFE-MAJ-001 precedent.
#
# IMPLEMENTATION NOTE: per-file evaluation envelope is identical to
# SCP-R-003 (single file at a time; `input.source_file` carries the
# path, `input.content` carries the text). Pattern 5 (entropy +
# dictionary-subtract) from RULE-005 §3.4 is DEFERRED to v1.4.0 —
# this implementation ships patterns 1-4 only (prefix / JWT-shape /
# AWS / Stripe-live).
package main

import rego.v1

scp_r_008_rule_id := "SCP-R-008"

scp_r_008_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/reviews/rule-proposals/RULE-005-secrets-not-in-committed-env-files.md",
])

# Closed exemption-by-filename set. Adding to this set requires a
# separate rule-RFC per RULE-005 §5 bypass-surface design.
scp_r_008_exempt_basenames := {
	".env.example",
	".env.template",
	".env.dist",
	".env.sample",
}

# Credential-pattern regexes. Patterns 1-4 from RULE-005 §3.1; pattern
# 5 (entropy + dictionary-subtract) deferred to v1.4.0+.
# All patterns anchor to the full VALUE string (post-trim).
scp_r_008_credential_patterns := [
	# Pattern 1: generic credential prefixes (case-insensitive).
	`^(?i)(sk_|pk_|api_|key_|token_|secret_|password_|pwd_)`,
	# Pattern 2: JWT shape — 3 base64url segments joined with `.`.
	`^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$`,
	# Pattern 3: AWS-style access key (exactly AKIA + 16 uppercase
	# alphanumerics = 20 chars total).
	`^AKIA[A-Z0-9]{16}$`,
	# Pattern 4: Stripe-live key.
	`^sk_live_[A-Za-z0-9]{24,}$`,
]

# Placeholder values to skip — known non-secrets.
scp_r_008_placeholder_values := {
	"",
	"changeme",
	"CHANGEME",
	"your-key-here",
	"<placeholder>",
	"PLACEHOLDER",
	"xxxx",
	"XXXX",
	"TODO",
	"TBD",
	"example",
	"EXAMPLE",
}

# True iff the given basename matches `^\.env(\..+)?$` (the env-file
# family) AND is NOT in the closed exemption set.
scp_r_008_is_env_basename(basename) if {
	regex.match(`^\.env(\..+)?$`, basename)
	not basename in scp_r_008_exempt_basenames
}

# Compute path basename. Mirrors SCP-R-003's basename helper.
scp_r_008_basename(path) := name if {
	parts := split(path, "/")
	name := parts[count(parts) - 1]
}

# Per-file applicability gate. Mirrors scp_r_003_manifest_input pattern.
scp_r_008_env_file_input if {
	source_file := object.get(input, "source_file", "")
	source_file != ""
	scp_r_008_is_env_basename(scp_r_008_basename(source_file))
	content := object.get(input, "content", "")
	is_string(content)
}

# Value-looks-like-credential helper. True if ANY of patterns 1-4 matches.
scp_r_008_value_looks_like_credential(value) if {
	some pattern in scp_r_008_credential_patterns
	regex.match(pattern, value)
}

# Strip surrounding double quotes if present (env files commonly write
# QUOTED values; the credential patterns expect unquoted content).
scp_r_008_unquote(value) := unquoted if {
	startswith(value, "\"")
	endswith(value, "\"")
	count(value) >= 2
	unquoted := substring(value, 1, count(value) - 2)
}

scp_r_008_unquote(value) := value if {
	not startswith(value, "\"")
}

scp_r_008_unquote(value) := value if {
	startswith(value, "\"")
	not endswith(value, "\"")
}

# Helper: per-line parse + filter. Returns the KEY+VALUE pair if the
# line is a non-comment KEY=VALUE row with a non-placeholder credential-
# pattern value; otherwise undefined. Extracted to keep the
# raw_findings rule body under Regal's max-rule-length threshold AND
# to keep the iteration `some line_idx, line in lines` idiom clean.
scp_r_008_line_credential_match(line) := {"key": key, "value": value} if {
	trimmed := trim_space(line)
	trimmed != ""
	not startswith(trimmed, "#")
	contains(trimmed, "=")
	parts := split(trimmed, "=")
	count(parts) >= 2
	key := trim_space(parts[0])
	key != ""
	value_raw := trim_space(concat("=", array.slice(parts, 1, count(parts))))
	value := scp_r_008_unquote(value_raw)
	not value in scp_r_008_placeholder_values
	scp_r_008_value_looks_like_credential(value)
}

# Helper: build credential-pattern finding object.
scp_r_008_credential_finding(source_file, line_idx, key, value) := finding if {
	finding := {
		"message": sprintf(
			"SCP-R-008 credential-pattern value in %s line %d: KEY=%s VALUE=<truncated 8 chars>%s...",
			[source_file, line_idx + 1, key, substring(value, 0, 8)],
		),
		"rule_id": scp_r_008_rule_id,
		"file": source_file,
		"line": line_idx + 1,
		"remediation_url": scp_r_008_remediation_url,
	}
}

# Per-line credential scan. Iterates content lines; emits one finding
# per offending line.
scp_r_008_raw_findings contains finding if {
	scp_r_008_env_file_input
	source_file := object.get(input, "source_file", "")
	content := object.get(input, "content", "")
	lines := split(content, "\n")
	some line_idx, line in lines
	match := scp_r_008_line_credential_match(line)
	finding := scp_r_008_credential_finding(source_file, line_idx, match.key, match.value)
}

# Public deny rule. Fires on raw findings not suppressed by waiver /
# rule-config. The workflow's WARN_BASELINE_RULES set (which carries
# SCP-R-008) demotes the deny to `::warning::` annotations + excludes
# SCP-R-008 from the merge-gate threshold check. The deny rule itself
# remains shape-parallel to SCP-R-001/002/003/004/007/012 so the future
# evidence-based promotion-to-deny decision (amended D-053 §Amendment
# point 1) flips only the workflow's warn-class set.
deny contains output if {
	some finding in scp_r_008_raw_findings
	not scp_active_waiver_for(scp_r_008_rule_id)
	not scp_rule_config_disabled(scp_r_008_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: active waiver against SCP-R-008.
warn contains record if {
	count(scp_r_008_raw_findings) > 0
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_008_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_008_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"finding_id": object.get(w, "finding_id", ""),
		"expires_at": object.get(w, "expires_at", ""),
		"file": object.get(input, "source_file", ""),
		"msg": sprintf(
			"%s suppressed by waiver (waiver_id=%s, expires_at=%s)",
			[scp_r_008_rule_id, object.get(w, "waiver_id", ""), object.get(w, "expires_at", "")],
		),
	}
}

# Suppression-observability warn: `.scp/rule-config.yaml disable: true`.
warn contains record if {
	count(scp_r_008_raw_findings) > 0
	scp_rule_config_disabled(scp_r_008_rule_id)
	cfg := scp_rule_config_entry(scp_r_008_rule_id)
	record := {
		"kind": "rule_config",
		"rule_id": scp_r_008_rule_id,
		"reason": "rule-config override",
		"expires_at": object.get(cfg, "expires_at", ""),
		"msg": sprintf(
			"%s suppressed by .scp/rule-config.yaml (expires_at=%s)",
			[scp_r_008_rule_id, object.get(cfg, "expires_at", "")],
		),
	}
}
