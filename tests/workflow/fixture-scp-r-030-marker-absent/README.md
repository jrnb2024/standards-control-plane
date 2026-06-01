<!-- not the adopter CLAUDE.md; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-030-marker-absent  ← LOAD-BEARING

WP-SCP-030 companion-activation selftest fixture — **row 2** of the SPEC §6 matrix,
the **non-negotiable coupling-guard assertion** (§4.1): an opted-in hooked adopter
whose `CLAUDE.md` lacks the canonical marker must emit a `::warning::` with the
**merge gate GREEN** — never a blocking deny.

This is the keystone of the whole activation: the reusable-workflow invocation runs
with `threshold: deny`, and the harness asserts its job result is **success** while
its summary carries the SCP-R-030 `marker_absent` deny finding. If SCP-R-030 were
NOT in both `WARN_BASELINE_RULES` sites, that finding would trip the threshold and
the job would FAIL — so `result == success` proves the coupling guard is airtight,
and the summary-finding proves the Option-A materialisation actually fires the rule.

- `rule-config.yaml` — `acc-hook-installed: true`.
- `repo/CLAUDE.md` — present, but the canonical marker is absent from the top 3 lines.
- `expected-annotations.json` — one SCP-R-030 `marker_absent` deny finding; gate green.
