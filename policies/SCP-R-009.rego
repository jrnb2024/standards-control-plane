# RULE: SCP-R-009 — auth-canonical-version-pin (WP-SCP-028; D-058 first
# auth-domain rule). Warn-baseline; deny-promote candidate at D-059.
#
# INTENT (plan §3.1): an adopter that consumes a ct-auth-{python,ts,go} SDK
# must pin a version >= CT's published minimum_secure_version. A pin strictly
# below that floor is a downgrade → DENY-class. A pin >= the floor but behind the
# published canonical_version is stale → WARN-class. LINKAGE-not-VALUES
# (D-049/D-058): the version numbers are READ from CT's signed
# canonical-sdk-versions manifest at evaluation time — never copied into this
# rule body.
#
# INPUT CONTRACT (materialised by the sibling companion workflow PR, NOT this
# WP — same dormancy pattern as SCP-R-006 / SCP-R-030):
#   input.canonical_sdk_versions          — parsed CT manifest (object); shape
#                                            per schemas/canonical-sdk-versions.schema.json
#   input.canonical_sdk_versions_verified — bool; true iff the workflow
#                                            cosign/Ed25519-verified the manifest
#                                            against its sibling .sig.bundle
#                                            (the REAL verification anchor)
#   input.adopter_ct_auth_deps            — array of {package, version, file}
#                                            the adopter pins (extracted from
#                                            pyproject.toml / package.json / go.mod)
#   input.rule_config                     — adopter .scp/rule-config.yaml (opt-out)
# Until the workflow materialises these, input is the per-file envelope where
# these keys are absent → every guard short-circuits → the rule VACUOUSLY
# PASSES (the SCP-R-006 safe-failure precedent). DORMANT until activation.
#
# FAIL-CLOSED (plan §3.1 deny-3 + §7.5; cosign deferral LIFTED 2026-06-05):
# if the manifest is present but NOT verified, the rule does not silently trust
# it — it emits a signature finding (deny-class, rendered as ::warning:: while
# SCP-R-009 is in WARN_BASELINE_RULES, so it never blocks an adopter merge on a
# CT-side signature hiccup; observability now, hard gate at D-059 deny-promote).
#
# Defines its OWN scp_r_009_* predicates per the SCP-R-004 SAFE-MAJ-001 /
# SCP-R-006 precedent (rule-local helpers preserve per-rule coverage; adding
# uncovered lines to scp_common.rego drops every rule below the 90% gate).
# Reuses ONLY the estate-wide suppression helpers scp_active_waiver_for +
# scp_rule_config_disabled from scp_common.rego.

package main

import rego.v1

scp_r_009_rule_id := "SCP-R-009"

scp_r_009_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md",
])

# Adopter opt-out (plan §2.3). Reads input.rule_config (the materialised
# adopter config), mirroring SCP-R-006's opt-in idiom. Default false = active.
default scp_r_009_opted_out := false

scp_r_009_opted_out if {
	rc := object.get(input, "rule_config", {})
	is_object(rc)
	object.get(rc, "auth-canonical-version-pin-disabled", false) == true
}

# True iff the workflow materialised a verified canonical manifest.
scp_r_009_manifest_verified if {
	object.get(input, "canonical_sdk_versions_verified", false) == true
}

# The CT manifest object (or {} when absent — dormant).
scp_r_009_manifest := manifest if {
	manifest := object.get(input, "canonical_sdk_versions", {})
	is_object(manifest)
}

# The ct-auth-* deps the adopter pins (or [] when absent — vacuous-pass).
scp_r_009_adopter_deps := deps if {
	deps := object.get(input, "adopter_ct_auth_deps", [])
	is_array(deps)
}

# Three-component semver → [major, minor, patch]. Undefined for non-semver
# (a malformed pin then yields no version finding for that dep; tracked-forward
# as a hardening item, acceptable at warn-baseline).
scp_r_009_semver(v) := parts if {
	is_string(v)
	raw := split(v, ".")
	count(raw) == 3
	parts := [to_number(raw[0]), to_number(raw[1]), to_number(raw[2])]
}

# Strict less-than over semver triples.
scp_r_009_lt(a, b) if {
	pa := scp_r_009_semver(a)
	pb := scp_r_009_semver(b)
	pa[0] < pb[0]
}

scp_r_009_lt(a, b) if {
	pa := scp_r_009_semver(a)
	pb := scp_r_009_semver(b)
	pa[0] == pb[0]
	pa[1] < pb[1]
}

scp_r_009_lt(a, b) if {
	pa := scp_r_009_semver(a)
	pb := scp_r_009_semver(b)
	pa[0] == pb[0]
	pa[1] == pb[1]
	pa[2] < pb[2]
}

# The canonical package entry the adopter dep maps to (or undefined).
scp_r_009_pkg_entry(dep) := entry if {
	pkg := object.get(dep, "package", "")
	pkg != ""
	packages := object.get(scp_r_009_manifest, "packages", {})
	is_object(packages)
	entry := object.get(packages, pkg, {})
	is_object(entry)
	entry != {}
}

# Finding builder (keeps the partial-rule bodies under Regal's length cap).
scp_r_009_finding(file, message) := {
	"rule_id": scp_r_009_rule_id,
	"file": file,
	"message": message,
	"remediation_url": scp_r_009_remediation_url,
}

# SEVERITY SPLIT (R1 CORR-MAJ-001): downgrade (below minimum_secure_version)
# + fail-closed are DENY-class → scp_r_009_deny_findings; stale (>= floor but
# behind canonical_version) is WARN-class → scp_r_009_warn_findings. They route
# to the `deny` / `warn` rules respectively, mirroring SCP-R-010/011. This
# matters at D-059 deny-promotion: a stale pin must NEVER block a merge — only
# a downgrade below the secure floor (minimum_secure_version) may.
#
# NOTE (R1 CG-MAJ-002): plan §3.1 deny-condition-2 ("adopter pins via SHA when
# CT declares a tagged-version constraint") is DEFERRED — it needs the
# companion workflow's pin-style extraction (the live canonical declares tagged
# versions, not SHAs), so it is a companion-materialisation concern, not a
# dormant-rule body concern. Tracked-forward FUP-WP-SCP-028-SHA-PIN-DETECT-001.

# --- deny-class: fail-closed (manifest present but unverified) -------------
# Distinguishes "no input at all" (dormant → vacuous) from "input present but
# the cosign chain did not verify" (do not silently trust → emit a finding).
scp_r_009_deny_findings contains finding if {
	count(scp_r_009_adopter_deps) > 0
	scp_r_009_manifest != {}
	not scp_r_009_manifest_verified
	finding := scp_r_009_finding(
		"canonical-sdk-versions.yaml",
		"SCP-R-009: CT canonical-sdk-versions manifest present but its signature did NOT verify (cosign/.sig.bundle anchor). Version conformance cannot be trusted; fail-closed. See CT contract-manifest-publish signing path.",
	)
}

# --- deny-class: adopter pins below CT's minimum_secure_version (downgrade) -
scp_r_009_deny_findings contains finding if {
	scp_r_009_manifest_verified
	some dep in scp_r_009_adopter_deps
	entry := scp_r_009_pkg_entry(dep)
	min_secure := object.get(entry, "minimum_secure_version", "")
	min_secure != ""
	version := object.get(dep, "version", "")
	scp_r_009_lt(version, min_secure)
	finding := scp_r_009_finding(
		object.get(dep, "file", "pyproject.toml"),
		sprintf(
			"SCP-R-009: %s pinned at %s is below CT's minimum_secure_version %s (downgrade-class). Pin >= %s. See CT canonical-sdk-versions.yaml.",
			[object.get(dep, "package", ""), version, min_secure, min_secure],
		),
	)
}

# --- warn-class: adopter pins stale (>= floor but behind canonical) -------
scp_r_009_warn_findings contains finding if {
	scp_r_009_manifest_verified
	some dep in scp_r_009_adopter_deps
	entry := scp_r_009_pkg_entry(dep)
	min_secure := object.get(entry, "minimum_secure_version", "")
	canonical := object.get(entry, "canonical_version", "")
	canonical != ""
	version := object.get(dep, "version", "")
	not scp_r_009_lt(version, min_secure)
	scp_r_009_lt(version, canonical)
	finding := scp_r_009_finding(
		object.get(dep, "file", "pyproject.toml"),
		sprintf(
			"SCP-R-009: %s pinned at %s is behind CT's canonical_version %s (stale). Consider bumping to %s. See CT canonical-sdk-versions.yaml.",
			[object.get(dep, "package", ""), version, canonical, canonical],
		),
	)
}

# True iff the rule produced ANY finding (deny or warn) — guards the
# suppression-observability records so a suppressed warn-only finding is still
# observable (R1 CORR-MIN-001 / CG-MIN-006).
scp_r_009_any_findings if {
	count(scp_r_009_deny_findings) > 0
}

scp_r_009_any_findings if {
	count(scp_r_009_warn_findings) > 0
}

# Public deny rule (downgrade + fail-closed). Warn-baseline membership in the
# workflow demotes these to ::warning:: + excludes from the merge-gate
# threshold; D-059 flips that.
deny contains output if {
	some finding in scp_r_009_deny_findings
	not scp_r_009_opted_out
	not scp_active_waiver_for(scp_r_009_rule_id)
	not scp_rule_config_disabled(scp_r_009_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Public warn rule (stale — inherently warn, never deny even post-D-059).
warn contains output if {
	some finding in scp_r_009_warn_findings
	not scp_r_009_opted_out
	not scp_active_waiver_for(scp_r_009_rule_id)
	not scp_rule_config_disabled(scp_r_009_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: active waiver against SCP-R-009.
warn contains record if {
	scp_r_009_any_findings
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_009_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_009_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"msg": sprintf("SCP-R-009 findings suppressed by active waiver %s", [object.get(w, "waiver_id", "")]),
	}
}

# Suppression-observability warn: `.scp/rule-config.yaml` disable or opt-out.
warn contains record if {
	scp_r_009_any_findings
	scp_rule_config_disabled(scp_r_009_rule_id)
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_009_rule_id,
		"msg": "SCP-R-009 findings suppressed by .scp/rule-config.yaml disable: true",
	}
}

warn contains record if {
	scp_r_009_any_findings
	scp_r_009_opted_out
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_009_rule_id,
		"msg": "SCP-R-009 findings suppressed by .scp/rule-config.yaml auth-canonical-version-pin-disabled: true",
	}
}
