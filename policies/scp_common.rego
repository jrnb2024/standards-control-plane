package main

import rego.v1

# Shared waiver-aware + rule-config-aware helpers used by every SCP-R-NNN
# rule. Loaded into the same `main` package so each rule references the
# helpers without an explicit import. Loaded into the per-rule opa test
# invocation by .github/workflows/policy-check.yml's coverage step.

# Time symbol for waiver and rule-config expiry checks. Tests mock this
# via `with main.scp_now_ns as <ns>`.
scp_now_ns := time.now_ns()

# True iff there's any active (unexpired) waiver in data.waivers whose
# rule_id matches. Conftest loads the caller's waivers file at
# `data.waivers` via the wrapper produced by lib/policy_check_invocation.sh.
#
# Spec note (WP-SCP-022 020C.1(i)): the spec reads "match by rule_id OR
# finding_id". finding_id matching requires per-finding correlation
# between the deny payload and the waiver, but the rego deny payload
# does not currently carry a finding_id. Implementing a blind
# finding_id-only match at the Rego layer would let any active
# finding-scoped waiver suppress denies for any rule — a silent-bypass
# hole. For 020C.1 the safe interpretation is rule_id-only suppression
# at this layer; finding_id correlation is deferred to WP-SCP-023's
# aggregator path where finding_ids are first-class. A finding_id-only
# waiver therefore fails closed — the deny still fires.
scp_active_waiver_for(rule_id) if {
	some w in scp_waivers
	is_object(w)
	object.get(w, "rule_id", "") == rule_id
	not scp_waiver_expired(w)
}

# True iff a waiver is expired. Fail-closed: missing or malformed
# expires_at => expired (suppression is denied). Otherwise compare
# parsed expires_at to scp_now_ns.
scp_waiver_expired(w) if {
	expires_at := object.get(w, "expires_at", "")
	expires_at == ""
}

scp_waiver_expired(w) if {
	expires_at := object.get(w, "expires_at", "")
	is_string(expires_at)
	expires_at != ""
	not scp_dateish_ns(expires_at)
}

scp_waiver_expired(w) if {
	expires_at := object.get(w, "expires_at", "")
	is_string(expires_at)
	expires_at != ""
	expiry_ns := scp_dateish_ns(expires_at)
	expiry_ns <= scp_now_ns
}

# All waiver entries currently loaded. Returns [] if data.waivers is
# missing or not an array.
scp_waivers := w if {
	candidate := object.get(data, "waivers", [])
	is_array(candidate)
	w := candidate
}

# True iff data.rule_config.rules[rule_id].disable == true. Per spec,
# expired rule-config still suppresses for one release; the workflow
# emits a separate ::warning:: annotation when expiry has passed.
scp_rule_config_disabled(rule_id) if {
	rule_cfg := scp_rule_config_entry(rule_id)
	object.get(rule_cfg, "disable", false) == true
}

# Returns the rule_config entry for a rule_id, or {} if absent. Used by
# warn rules to attach metadata (expires_at, etc.) to observability records.
scp_rule_config_entry(rule_id) := entry if {
	rules := object.get(object.get(data, "rule_config", {}), "rules", {})
	entry := object.get(rules, rule_id, {})
}

# Date-or-date-time string parser. Mirrors SCP-R-002's scp_r_002_dateish_ns
# so callers can express expiry as either form.
scp_dateish_ns(value) := ns if {
	is_string(value)
	regex.match(`^[0-9]{4}-[0-9]{2}-[0-9]{2}$`, value)
	ns := time.parse_rfc3339_ns(sprintf("%sT00:00:00Z", [value]))
}

scp_dateish_ns(value) := ns if {
	is_string(value)
	regex.match(`^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$`, value)
	ns := time.parse_rfc3339_ns(value)
}
