# RULE: SCP-R-031 — Estate-context bootstrap marker linkage (WP-ESC-012b;
# D-058 canonical-conformance; control-tower authority domain).
#
# Gates that a repo which opts in to the Estate-context bootstrap contract
# carries the canonical marker in BOTH its CLAUDE.md AND its AGENTS.md.
# control-tower OWNS + authors the contract (contracts/estate-context-marker.md,
# estate-context-bootstrap v1); SCP gates LINKAGE to it — SCP never becomes
# the Estate-context authority (D-058 anti-pattern). LINKAGE-not-VALUES: this
# rule checks for the PRESENCE of the canonical marker in the top-of-file block
# of each instruction file, never the repo's specific Estate content.
#
# Two files, one marker: the estate spine reaches BOTH agent-instruction
# surfaces (Claude Code reads CLAUDE.md; Codex / other agents read AGENTS.md),
# so BOTH must carry the static bootstrap marker or a session on the un-marked
# surface never learns the estate operating context. This is the whole point
# vs SCP-R-030 (which gates CLAUDE.md only).
#
# STATIC-MARKER invariant: the instruction files carry ONLY the static marker,
# never dynamic Estate state (workspace_id / org_id / principal / content
# digests / freshness / expiry / watermark). Dynamic state belongs to the
# live Estate-context plane, not a committed instruction file — a leaked
# dynamic token means the file is being used as a state channel (drift +
# stale-context hazard). The negative check fires on any forbidden token in
# the top-of-file block.
#
# Ships at WARN BASELINE (advisory). Add SCP-R-031 to the workflow
# WARN_BASELINE_RULES set + version-manifest.json in THIS PR; the companion
# workflow PR materialises input.rule_config + input.claude_md* +
# input.agents_md* into the evaluation envelope and adds SCP-R-031 to the
# REPO_LEVEL_RULES eval set. Until that companion PR lands, input.rule_config
# is absent under the per-file envelope the existing rules use, so this rule
# VACUOUSLY PASSES (the SCP-R-006/030 safe-failure precedent). Deny-promotion
# of the marker-absent condition is reserved for a later operator decision
# (mirrors SCP-R-030's D-060 note); do NOT put SCP-R-031 in any deny set.
#
# Defines its OWN scp_r_031_* predicates per the SCP-R-004 SAFE-MAJ-001
# precedent. Reuses the shared suppression helpers from scp_common.rego
# (scp_active_waiver_for + scp_rule_config_disabled + scp_rule_config_entry).
package main

import rego.v1

scp_r_031_rule_id := "SCP-R-031"

scp_r_031_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/plans/WP-SCP-031-estate-context-marker-linkage-v1.md",
])

# The canonical marker string, ratified VERBATIM by control-tower (the
# Estate-context authority) in contracts/estate-context-marker.md. SCP-R-031
# greps for exactly this substring (the LINKAGE target). A future contract
# revision becomes v2; a v1-only marker then fails this exact-substring check
# during the migration window — intended.
scp_r_031_canonical_marker := "<!-- canonical:estate-context-bootstrap v1 -->"

# Forbidden dynamic-Estate tokens. Presence of any of these in the top-of-file
# block means the instruction file is carrying LIVE Estate state instead of
# the static marker (STATIC-MARKER invariant). Kept small + high-signal:
# identity (workspace_id / org_id / principal), content-integrity (sha256: /
# digest), and freshness (freshness / expires_at / observed_at / watermark).
scp_r_031_forbidden_tokens := {
	"workspace_id",
	"org_id",
	"principal",
	"sha256:",
	"digest",
	"freshness",
	"expires_at",
	"observed_at",
	"watermark",
}

# Adopter opt-in gate. Reads input.rule_config (NOT data.rule_config — that
# namespace carries the generic disable path via scp_common). Mirrors
# scp_r_030_opted_in. Vacuous-false when input.rule_config is absent
# (production per-file envelope), so the rule vacuously passes until the
# companion workflow PR materialises the inputs. Safe-failure mode.
scp_r_031_opted_in if {
	rc := object.get(input, "rule_config", {})
	is_object(rc)
	object.get(rc, "estate-context-marker", false) == true
}

# CLAUDE.md / AGENTS.md presence flags, materialised by the companion workflow
# PR alongside input.rule_config. Default false keeps the rule vacuous-safe.
scp_r_031_claude_md_present if {
	object.get(input, "claude_md_present", false) == true
}

scp_r_031_agents_md_present if {
	object.get(input, "agents_md_present", false) == true
}

# CLAUDE.md text content. Total function: the string when present, "" when
# absent OR present-but-non-string (null/number/object). Keeps every
# downstream helper defined rather than undefined on a malformed input
# (mirrors SCP-R-030's two-clause idiom).
scp_r_031_claude_md_content := content if {
	content := object.get(input, "claude_md", "")
	is_string(content)
}

scp_r_031_claude_md_content := "" if {
	not is_string(object.get(input, "claude_md", ""))
}

# AGENTS.md text content — the parallel total function keyed on input.agents_md.
scp_r_031_agents_md_content := content if {
	content := object.get(input, "agents_md", "")
	is_string(content)
}

scp_r_031_agents_md_content := "" if {
	not is_string(object.get(input, "agents_md", ""))
}

# LINKAGE target: the exact ratified marker substring appears within the first
# 5 lines. Anchoring to the top-of-file (rather than substring-anywhere)
# defeats a buried / code-fenced marker that would otherwise spoof the gate
# without a real top-of-file bootstrap block. Window 5 (vs SCP-R-030's 3)
# allows a short title/front-matter line above the marker on either surface.
scp_r_031_claude_has_marker if {
	lines := array.slice(split(scp_r_031_claude_md_content, "\n"), 0, 5)
	some line in lines
	contains(line, scp_r_031_canonical_marker)
}

scp_r_031_agents_has_marker if {
	lines := array.slice(split(scp_r_031_agents_md_content, "\n"), 0, 5)
	some line in lines
	contains(line, scp_r_031_canonical_marker)
}

# Dynamic-state negative check: any forbidden dynamic-Estate token appears
# within the top 5-line block. Anchored to the same top-of-file window as the
# marker check, so a forbidden token buried far below does not trip it (the
# leak that matters is one in the bootstrap block masquerading as context).
scp_r_031_claude_dynamic_state if {
	block := concat("\n", array.slice(split(scp_r_031_claude_md_content, "\n"), 0, 5))
	some tok in scp_r_031_forbidden_tokens
	contains(block, tok)
}

scp_r_031_agents_dynamic_state if {
	block := concat("\n", array.slice(split(scp_r_031_agents_md_content, "\n"), 0, 5))
	some tok in scp_r_031_forbidden_tokens
	contains(block, tok)
}

# Finding builder. `file` names the offending instruction file (CLAUDE.md or
# AGENTS.md) so a two-file adopter learns exactly which surface to fix.
scp_r_031_finding(file, code, message) := finding if {
	finding := {
		"rule_id": scp_r_031_rule_id,
		"file": file,
		"code": code,
		"message": message,
		"remediation_url": scp_r_031_remediation_url,
	}
}

# marker_absent (CLAUDE.md) — opted in, CLAUDE.md present but missing the marker.
# (Deny-class condition reserved for a later operator decision; warn here.)
scp_r_031_raw_findings contains finding if {
	scp_r_031_opted_in
	scp_r_031_claude_md_present
	not scp_r_031_claude_has_marker
	finding := scp_r_031_finding(
		"CLAUDE.md",
		"marker_absent",
		sprintf("SCP-R-031: %s lacks the canonical Estate-context bootstrap marker '%s' (expected in the top-of-file block). control-tower owns the contract (contracts/estate-context-marker.md); SCP gates linkage. See docs/plans/WP-SCP-031-estate-context-marker-linkage-v1.md.", ["CLAUDE.md", scp_r_031_canonical_marker]),
	)
}

# marker_absent (AGENTS.md) — opted in, AGENTS.md present but missing the marker.
# This is the second-file teeth that SCP-R-030 does not have.
scp_r_031_raw_findings contains finding if {
	scp_r_031_opted_in
	scp_r_031_agents_md_present
	not scp_r_031_agents_has_marker
	finding := scp_r_031_finding(
		"AGENTS.md",
		"marker_absent",
		sprintf("SCP-R-031: %s lacks the canonical Estate-context bootstrap marker '%s' (expected in the top-of-file block). control-tower owns the contract (contracts/estate-context-marker.md); SCP gates linkage. See docs/plans/WP-SCP-031-estate-context-marker-linkage-v1.md.", ["AGENTS.md", scp_r_031_canonical_marker]),
	)
}

# dynamic_state (CLAUDE.md) — opted in, a forbidden dynamic-Estate token leaked
# into the CLAUDE.md top block. Independent of marker presence: a file may
# carry the marker AND leak dynamic state.
scp_r_031_raw_findings contains finding if {
	scp_r_031_opted_in
	scp_r_031_claude_md_present
	scp_r_031_claude_dynamic_state
	finding := scp_r_031_finding(
		"CLAUDE.md",
		"dynamic_state",
		sprintf("SCP-R-031: %s carries dynamic Estate state; instruction files must carry only the static marker. Remove the dynamic Estate token from the top-of-file block. See docs/plans/WP-SCP-031-estate-context-marker-linkage-v1.md.", ["CLAUDE.md"]),
	)
}

# dynamic_state (AGENTS.md) — the parallel check for the AGENTS.md surface.
scp_r_031_raw_findings contains finding if {
	scp_r_031_opted_in
	scp_r_031_agents_md_present
	scp_r_031_agents_dynamic_state
	finding := scp_r_031_finding(
		"AGENTS.md",
		"dynamic_state",
		sprintf("SCP-R-031: %s carries dynamic Estate state; instruction files must carry only the static marker. Remove the dynamic Estate token from the top-of-file block. See docs/plans/WP-SCP-031-estate-context-marker-linkage-v1.md.", ["AGENTS.md"]),
	)
}

# Public deny rule. Fires on raw findings not suppressed by waiver /
# rule-config-disable. The companion workflow PR's WARN_BASELINE_RULES set
# demotes these denies to ::warning:: annotations + excludes SCP-R-031 from
# the merge-gate threshold check (warn baseline). Shape-parallel to
# SCP-R-030 so a future deny-promotion flips only the workflow's warn-class set.
deny contains output if {
	some finding in scp_r_031_raw_findings
	not scp_active_waiver_for(scp_r_031_rule_id)
	not scp_rule_config_disabled(scp_r_031_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: active waiver against SCP-R-031.
warn contains record if {
	count(scp_r_031_raw_findings) > 0
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_031_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_031_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"expires_at": object.get(w, "expires_at", ""),
		"msg": sprintf(
			"%s suppressed by waiver (waiver_id=%s, expires_at=%s)",
			[scp_r_031_rule_id, object.get(w, "waiver_id", ""), object.get(w, "expires_at", "")],
		),
	}
}

# Suppression-observability warn: `.scp/rule-config.yaml disable: true` (the
# auditable + expiring reversible path).
warn contains record if {
	count(scp_r_031_raw_findings) > 0
	scp_rule_config_disabled(scp_r_031_rule_id)
	cfg := scp_rule_config_entry(scp_r_031_rule_id)
	record := {
		"kind": "rule_config",
		"rule_id": scp_r_031_rule_id,
		"reason": "rule-config override",
		"expires_at": object.get(cfg, "expires_at", ""),
		"msg": sprintf(
			"%s suppressed by .scp/rule-config.yaml (expires_at=%s)",
			[scp_r_031_rule_id, object.get(cfg, "expires_at", "")],
		),
	}
}
