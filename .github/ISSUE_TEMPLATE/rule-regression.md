---
name: Rule regression report
about: Report an SCP federation primitive rule regression (false positive, false negative, or runtime failure)
title: "[regression] SCP-R-NNN: <one-line summary>"
labels: ["rule-regression", "needs-triage"]
assignees:
  - jrnb2024
---

<!--
WP-SCP-022 020H.1 (iv-a): adopter-reported regression channel.
Target: 4 hours from report to tag-pin revert if confirmed.

Use this template when:
- An SCP rule (SCP-R-001..SCP-R-NNN) fires on a manifest that should
  pass (false positive).
- An SCP rule fails to fire on a manifest that should be denied
  (false negative).
- The reusable workflow itself fails at runtime (SCP-E001..SCP-E007)
  in a way that wasn't caught by the SHA-locked binary verification.
- The conflict-gate disagrees (SCP-E005) on a fixture that previously
  agreed.
- The weekly canary-replay workflow (canary-replay.yml) opened this
  issue automatically — leave the auto-generated body intact and add
  whatever context you have.

Do NOT use this template for:
- Feature requests or proposed new rules — file a rule proposal
  under docs/reviews/rule-proposals/ instead.
- Adopter-side configuration questions — open a discussion or tag
  @jrnb2024 directly.
- Security-bypass disclosures — see `SECURITY.md` at the repo root
  (private GitHub Security Advisory or `jimbrooke@me.com`); do NOT
  file a public regression issue for these.
-->

## Affected SCP version

- SCP federation primitive `# tag:` pin in your wrapper: `v<X>.<Y>.<Z>`
- Wrapper `@<commit-SHA>` pin: `<40-char SHA>`
- Approximate date you started seeing the regression: `YYYY-MM-DD`
- (If known) last working `# tag:`: `v<X>.<Y>.<Z-1>`

## Affected rule(s)

- [ ] `SCP-R-001` (auth contract)
- [ ] `SCP-R-002` (waivers shape)
- [ ] `SCP-R-003` (no-manifest-applicable observability)
- [ ] Other / runtime: <error code or job name>

## Regression class

- [ ] False positive — rule fires on a manifest that should pass.
- [ ] False negative — rule fails to fire on a manifest that should be denied.
- [ ] Runtime / infra — `SCP-E001`..`SCP-E007` annotation surfaced unexpectedly.
- [ ] Conflict-gate disagreement (`SCP-E005`) — Rego ≠ Python on a previously-agreeing fixture.
- [ ] Auto-detected by `canary-replay.yml` — divergence from baseline (paste the workflow run URL below).

## Symptom

What did you observe? Paste the relevant `::error::` / `::warning::`
annotation, the workflow-run URL, and (if redactable) the manifest
that triggered the regression.

```
<paste annotation or log excerpt here>
```

Workflow run URL: `<link to the failing run>`

## Expected behaviour

What did you expect to happen? Cite the rule's specification at
`docs/reviews/rule-proposals/RULE-NNN.md` (if filed) or
`policies/<rule-id>.rego` (the Rego header comment).

## Reproduction

Minimum manifest snippet that reproduces the regression. Redact any
sensitive content; the SCP self-dogfood gate will run on this snippet
during triage.

```yaml
<paste minimal manifest snippet here>
```

If you can't share the manifest publicly, write "private — DM
@jrnb2024 for redacted reproduction" and we'll handle it out-of-band.

## Adopter-side impact

- Number of PRs blocked / mis-labelled: `<count>`
- Production-blocking? `yes` / `no` / `unsure`
- Have you applied a temporary workaround? (e.g. waiver entry,
  rule-config disable, wrapper SHA pin reverted) — describe.

## Triage checklist (SCP maintainer fills in)

- [ ] Reproduced locally via `scripts/scp-policy-check`.
- [ ] Workflow-run timeline confirms the regression window.
- [ ] Conflict-gate fixture added under `tests/conflict_gate/<rule-id>/`.
- [ ] Root cause identified: spec / implementation / SCP-side dependency / adopter-side environment.
- [ ] Fix path: PATCH (revert + re-implement) | MINOR (re-spec via rule-proposal) | MAJOR (deprecation ramp + amending decision).
- [ ] Tag-pin revert decision (target: ≤4h from report). If reverted, name the prior good `v<X>.<Y>.<Z>`.
- [ ] Estate-cascade impact assessed (which adopters are pinned at the affected version range?).
- [ ] Issue closed with a link to the fix PR + post-incident note.

---

References:
- ADOPT-001 §12.7.5 (rollback procedure — 4h target).
- `policies/VERSIONING.md` (semver contract; PATCH vs MINOR vs MAJOR fix path).
- `docs/reviews/rule-proposals/README.md` (when a regression motivates a re-spec rather than a patch).
