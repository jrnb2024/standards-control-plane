# RULE: SCP-R-030 — hooked-repo onboarding conformance (WP-SCP-030
# Layer 2; D-058 second domain / proving ground).
#
# Gates that a repo which runs the acc-hook (ACC kernel PreToolUse hook)
# carries the canonical "hooked-repo onboarding preamble" in its
# CLAUDE.md. ACC owns the acc-hook AND authors + ratifies the canonical
# contract (docs/guides/hooked-repo-onboarding-preamble.md,
# acc-hook-onboarding v1). SCP gates LINKAGE to it; SCP never becomes
# the hook authority (D-058 anti-pattern). LINKAGE-not-VALUES: this rule
# checks for the PRESENCE + shape of the canonical preamble, never the
# repo's specific ceremony (CT four-tier Codex dispatch vs SCP Pattern-3
# session-start dispatch are BOTH accepted).
#
# Ships at WARN BASELINE (WP-SCP-030 §2.2.3). Add SCP-R-030 to the
# workflow WARN_BASELINE_RULES set + materialise input.rule_config +
# input.claude_md* in the companion workflow PR; deny-promotion of the
# marker-absent condition is reserved for D-060 (post-4-week observation).
#
# TRIGGER WRINKLE (WP-SCP-030 §4): .claude/settings.json is gitignored
# estate-wide, so a Rego rule evaluating the checked-out tree cannot read
# it to learn the repo is hooked. The trigger is therefore option (a):
# a committed opt-in `.scp/rule-config.yaml acc-hook-installed: true`,
# read from input.rule_config (mirrors SCP-R-006 acc-cross-repo-caller-
# scoped). Until the companion workflow PR materialises input.rule_config
# + input.claude_md* into the evaluation envelope, input.rule_config is
# absent under the per-file envelope the existing rules use, so this rule
# VACUOUSLY PASSES (the SCP-R-006 safe-failure precedent). The SCP-self
# dogfood (acc-hook-installed: true) is proven by the PASS test fixture,
# not by a live CI finding, until that companion PR lands.
#
# Defines its OWN scp_r_030_* predicates per the SCP-R-004 SAFE-MAJ-001
# precedent. Reuses the shared suppression helpers from scp_common.rego
# (scp_active_waiver_for + scp_rule_config_disabled + scp_rule_config_entry).
package main

import rego.v1

scp_r_030_rule_id := "SCP-R-030"

scp_r_030_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/plans/WP-SCP-030-hooked-repo-onboarding-conformance-v1.md",
])

# The canonical marker string, ratified VERBATIM by ACC (the acc-hook
# authority) in docs/guides/hooked-repo-onboarding-preamble.md. SCP-R-030
# greps for exactly this substring (the LINKAGE target). A future contract
# revision becomes v2; a v1-only marker then fails this exact-substring
# check during the migration window — intended.
scp_r_030_canonical_marker := "<!-- canonical:acc-hook-onboarding v1 -->"

# Adopter opt-in gate. Reads input.rule_config (NOT data.rule_config —
# that namespace carries the generic disable path via scp_common). Mirrors
# scp_r_006_acc_scoped. Vacuous-false when input.rule_config is absent
# (production per-file envelope), so the rule vacuously passes until the
# companion workflow PR materialises the inputs. Safe-failure mode.
scp_r_030_opted_in if {
	rc := object.get(input, "rule_config", {})
	is_object(rc)
	object.get(rc, "acc-hook-installed", false) == true
}

# CLAUDE.md presence flag, materialised by the companion workflow PR
# alongside input.rule_config. Default false keeps the rule vacuous-safe.
scp_r_030_claude_md_present if {
	object.get(input, "claude_md_present", false) == true
}

# CLAUDE.md text content. Total function: the string when present, ""
# when absent OR present-but-non-string (null/number/object). Keeps every
# downstream helper defined rather than undefined on a malformed input
# (R1 CORR-MAJ-001; mirrors the `default`/multi-clause idiom in
# scp_common.rego + scp_r_008_unquote).
scp_r_030_claude_md_content := content if {
	content := object.get(input, "claude_md", "")
	is_string(content)
}

scp_r_030_claude_md_content := "" if {
	not is_string(object.get(input, "claude_md", ""))
}

# LINKAGE target: the exact ratified marker substring appears within the
# first 3 lines. ACC contract element 1 mandates "the marker on line 1";
# all 6 hooked repos place it there. Anchoring to the top-of-file (rather
# than substring-anywhere) defeats a buried / code-fenced marker that would
# otherwise spoof the gate without a real top-of-file preamble (R1 SB-MAJ-001).
scp_r_030_has_marker if {
	lines := array.slice(split(scp_r_030_claude_md_content, "\n"), 0, 3)
	some line in lines
	contains(line, scp_r_030_canonical_marker)
}

# Element 3 — always-allowed path list. Heuristic (warn-baseline; cheap):
# the case-insensitive "always-allowed" qualifier AND the docs/** glob.
scp_r_030_has_always_allowed if {
	regex.match(`(?i)always-allowed`, scp_r_030_claude_md_content)
	contains(scp_r_030_claude_md_content, "docs/**")
}

# Element 4 — a ceremony pointer. LINKAGE-not-VALUES: accept ANY repo's
# ceremony — CT four-tier Codex "dispatch"; SCP Pattern-3
# "scripts/operator/scp-pattern3-dispatch.sh". Substring dispatch OR scripts/.
scp_r_030_has_ceremony if {
	contains(scp_r_030_claude_md_content, "dispatch")
}

scp_r_030_has_ceremony if {
	contains(scp_r_030_claude_md_content, "scripts/")
}

# Element 5 — the never-disable rule (D-057). Heuristic: a never/not/
# forbidden qualifier within 60 same-line chars of "disabl" (either order).
scp_r_030_has_never_disable if {
	regex.match(`(?i)(never|not|forbidden|don.t)[^\n]{0,60}disabl`, scp_r_030_claude_md_content)
}

scp_r_030_has_never_disable if {
	regex.match(`(?i)disabl[^\n]{0,60}(forbidden|never)`, scp_r_030_claude_md_content)
}

# Finding builder. All SCP-R-030 findings are CLAUDE.md-scoped.
scp_r_030_finding(code, message) := finding if {
	finding := {
		"rule_id": scp_r_030_rule_id,
		"file": "CLAUDE.md",
		"code": code,
		"message": message,
		"remediation_url": scp_r_030_remediation_url,
	}
}

# claude_md_absent — opted in but no CLAUDE.md in the checked-out tree.
scp_r_030_raw_findings contains finding if {
	scp_r_030_opted_in
	not scp_r_030_claude_md_present
	finding := scp_r_030_finding(
		"claude_md_absent",
		"SCP-R-030: repo opted in (acc-hook-installed: true) but CLAUDE.md is absent — it must carry the canonical onboarding preamble. See ACC docs/guides/hooked-repo-onboarding-preamble.md (acc-hook-onboarding v1).",
	)
}

# marker_absent — CLAUDE.md present but missing the ratified marker.
# (Deny-class condition reserved for D-060; ships at warn here.)
scp_r_030_raw_findings contains finding if {
	scp_r_030_opted_in
	scp_r_030_claude_md_present
	not scp_r_030_has_marker
	finding := scp_r_030_finding(
		"marker_absent",
		sprintf("SCP-R-030: CLAUDE.md lacks the canonical onboarding marker '%s' (expected on line 1). ACC authors the contract; SCP gates linkage. See ACC docs/guides/hooked-repo-onboarding-preamble.md.", [scp_r_030_canonical_marker]),
	)
}

# element_missing:always-allowed — marker present, always-allowed list absent.
scp_r_030_raw_findings contains finding if {
	scp_r_030_opted_in
	scp_r_030_claude_md_present
	scp_r_030_has_marker
	not scp_r_030_has_always_allowed
	finding := scp_r_030_finding(
		"element_missing:always-allowed",
		"SCP-R-030: onboarding preamble present but missing the always-allowed path list (expected an 'always-allowed' heading + the docs/** glob). See preamble element 3.",
	)
}

# element_missing:ceremony — marker present, no ceremony pointer.
scp_r_030_raw_findings contains finding if {
	scp_r_030_opted_in
	scp_r_030_claude_md_present
	scp_r_030_has_marker
	not scp_r_030_has_ceremony
	finding := scp_r_030_finding(
		"element_missing:ceremony",
		"SCP-R-030: onboarding preamble present but missing a self-build ceremony pointer (expected a 'dispatch' or 'scripts/' reference). LINKAGE-not-VALUES: any repo ceremony is accepted. See preamble element 4.",
	)
}

# element_missing:never-disable — marker present, no never-disable rule.
scp_r_030_raw_findings contains finding if {
	scp_r_030_opted_in
	scp_r_030_claude_md_present
	scp_r_030_has_marker
	not scp_r_030_has_never_disable
	finding := scp_r_030_finding(
		"element_missing:never-disable",
		"SCP-R-030: onboarding preamble present but missing the never-disable rule (D-057: a tripped session declares scope or asks the operator; it does NOT disable enforcement). See preamble element 5.",
	)
}

# Public deny rule. Fires on raw findings not suppressed by waiver /
# rule-config-disable. The companion workflow PR's WARN_BASELINE_RULES
# set demotes these denies to ::warning:: annotations + excludes
# SCP-R-030 from the merge-gate threshold check (warn baseline). Shape-
# parallel to SCP-R-001/002/003/004/007/008 so the future D-060
# deny-promotion flips only the workflow's warn-class set.
deny contains output if {
	some finding in scp_r_030_raw_findings
	not scp_active_waiver_for(scp_r_030_rule_id)
	not scp_rule_config_disabled(scp_r_030_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: active waiver against SCP-R-030.
warn contains record if {
	count(scp_r_030_raw_findings) > 0
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_030_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_030_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"expires_at": object.get(w, "expires_at", ""),
		"msg": sprintf(
			"%s suppressed by waiver (waiver_id=%s, expires_at=%s)",
			[scp_r_030_rule_id, object.get(w, "waiver_id", ""), object.get(w, "expires_at", "")],
		),
	}
}

# Suppression-observability warn: `.scp/rule-config.yaml disable: true`
# (the auditable + expiring reversible path; SCP-R-030 §2.2.5).
warn contains record if {
	count(scp_r_030_raw_findings) > 0
	scp_rule_config_disabled(scp_r_030_rule_id)
	cfg := scp_rule_config_entry(scp_r_030_rule_id)
	record := {
		"kind": "rule_config",
		"rule_id": scp_r_030_rule_id,
		"reason": "rule-config override",
		"expires_at": object.get(cfg, "expires_at", ""),
		"msg": sprintf(
			"%s suppressed by .scp/rule-config.yaml (expires_at=%s)",
			[scp_r_030_rule_id, object.get(cfg, "expires_at", "")],
		),
	}
}
