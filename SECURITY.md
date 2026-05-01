# Security policy

**Status:** v1.0.0 stub (closes WP-SCP-022 020H.1 R1 SAFE-MAJ-003).
**Closes:** WP-SCP-020 §4.1 follow-up SCP-073.sec.

## Reporting a vulnerability

If you discover a vulnerability in the SCP federation primitive — including, but not limited to:

- a **policy-bypass** that allows a deny-shaped manifest to merge without the three-gate break-glass (CODEOWNERS approval + sibling D-NNN row + matching `waivers.json` entry per ADOPT-001 §12.7.4);
- a **bypass-by-omission** that lets a manifest evade an `SCP-R-NNN` rule by structural exemption rather than waiver;
- a **supply-chain compromise** of the SCP source (the reusable workflow, the Renovate preset, `scripts/scp-policy-check.lock`, `scripts/.tool-versions`, or any `vendor/` binary);
- a **branch-protection bypass** on the SCP repo itself (e.g. tag-protection ruleset evasion);
- a **runner-side compromise** affecting the OPA / Conftest / Regal binary chain or the freshness-warning fetch path;

please **DO NOT file a public GitHub issue**.

Instead:

1. **Open a private GitHub Security Advisory** at <https://github.com/jrnb2024/standards-control-plane-/security/advisories/new>. This is the preferred channel — the advisory mechanism gives the maintainer a private workspace to triage and patch without disclosing the issue. (Operator one-time setup: confirm Private Vulnerability Reporting is enabled via repo Settings → Security → Private vulnerability reporting → Enable; verify with `gh api repos/jrnb2024/standards-control-plane-/security-advisories` returning HTTP 200 with `[]` or an advisory list.)

2. **Or email the maintainer directly:** `jimbrooke@me.com`. Use the subject line `SCP federation primitive — security disclosure`. The maintainer will acknowledge within **3 business days** (single-operator constraint per D-031; the 2026-07-21 quarterly bus-factor review re-evaluates this SLA).

## What to include

- A clear description of the issue and the impact you observed.
- Reproduction steps or a minimum manifest snippet (redacted if necessary).
- The affected SCP version (`# tag:` pin from your wrapper, plus the wrapper `@<commit-SHA>` pin).
- Your assessment of severity (CRIT / MAJ / MIN per the WP-SCP-022 review-finding scale, or a free-form description).
- Whether you're willing to be named in the eventual public advisory + post-incident note (default: anonymised).

## What to expect

- **Initial response within 3 business days.** Acknowledgement of receipt + a triage estimate.
- **Coordinated disclosure window:** target 30 days from initial response to public advisory + patch release. Extensions for complex multi-party fixes are possible; the maintainer will coordinate with you.
- **Credit in the advisory:** named (with permission) or anonymous, your choice.

## What is in scope

- The SCP federation primitive at this repository: `https://github.com/jrnb2024/standards-control-plane-`.
- Any release tag `v1.0.0` and forward, plus `main` HEAD.
- The Renovate preset published at `renovate/v*` tag series.
- Any artefact that ships in a published release: the reusable workflow, the canary-replay cron, the rule-regression issue template, the rule-RFC process, the version manifest.

## What is out of scope

- Vulnerabilities in OPA, Conftest, or Regal upstream — file with their respective projects.
- Vulnerabilities in adopter repositories that misconfigure the SCP wrapper. (If you believe the misconfiguration is enabled by an adopter-facing documentation gap in `docs/adoption/ADOPT-001-project-onboarding.md`, that IS in scope.)
- Renovate Bot or GitHub Actions platform vulnerabilities — file with the respective vendors.
- Cryptographic primitives in the underlying tools.

## Public advisory cadence

When a security issue is patched and disclosed:

- A **GitHub Security Advisory** with CVE-ID (where applicable) is published.
- A **post-incident note** is added to `docs/security/incidents/` (created on first incident) summarising root cause, fix, adopter migration, and timeline.
- Affected adopters are notified via the Renovate preset's automated bump if the fix lands as a tagged release; out-of-band notification is sent for reachable estate adopters (FLA, PIM, recommender, shopify-app, mapp-doc-agent, control-tower per WP-SCP-024).

## References

- ADOPT-001 §12.7.8 — adopter-facing security pointer.
- `.github/ISSUE_TEMPLATE/rule-regression.md` — public rule-regression channel (NOT for security bypass disclosures).
- `policies/VERSIONING.md` — semver contract; security fixes typically ship as PATCH or MINOR.
- WP-SCP-020 plan §4.1 follow-up SCP-073.sec — the spec line that this stub closes.
