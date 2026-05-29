# Operator runbook — SCP-wrapper bump sweep (monthly)

**Status:** ACTIVE (ratified 2026-05-29 via `FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001` option (c) closure).
**Audience:** the SCP operator running the monthly cohort-adopter SCP-wrapper SHA bump.
**Companion script:** `scripts/operator/scp-wrapper-bump-sweep.sh`.

---

## Why this exists

SCP cohort adopters pin a 40-char SHA on the `uses:` clause of their `.github/workflows/policy-check-wrapper.yml`. **Renovate / Dependabot is NOT wired estate-wide.** The BACKLOG analysis (`FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001`) enumerated three options:

- **(a) Renovate App org-wide** — single config, auto-bumps; but `postUpgradeTasks` (needed to mirror `scp-sha:` per axis-I) requires admin-level self-host or Mend's premium tier. Free tier ships PR with mismatched `scp-sha:` → CI fails closed → operator manually edits the PR. Net: doesn't actually save operator effort.
- **(b) Dependabot per-repo** — matches SCP-self's pattern; no org approval; but **no** post-upgrade hooks (every bump needs manual `scp-sha:` edit) AND 5× config maintenance.
- **(c) Operator-attended monthly cycle** — zero CI/bot infrastructure to maintain; explicit; auditable; this runbook is the procedure. Vulnerable to operator vacation/illness gaps. **← chosen 2026-05-29 for the current estate scale (3 LIVE adopters; well below 8-10 trigger).**

Revisit when the estate exceeds 8-10 adopters OR if the monthly cadence misses 2+ adopters in a single quarter.

---

## When to run the sweep

- **Monthly** — first business day of each month is a fine cadence.
- **After any SCP release tag** — re-pin adopters to the new release SHA.
- **After any kernel-dangerous change to SCP main** (e.g. a `policy-check.yml` workflow update) — pull adopters forward so they exercise the new behaviour at their next PR.

---

## The procedure

### Step 1 — Survey current state (read-only, ~10s)

```bash
cd ~/Projects/standards-control-plane
scripts/operator/scp-wrapper-bump-sweep.sh
```

The script:

- Resolves SCP main HEAD SHA via `gh api`.
- For each LIVE adopter (hardcoded list in the script; currently PIM + CT + mapp-doc-agent), pulls `.github/workflows/policy-check-wrapper.yml` via `gh api` and parses the `@<SHA>` pin AND the `scp-sha:` input.
- Reports per-adopter: current pin, `scp-sha:` input, ✅ current / 📦 needs-bump / ⚠️ axis-I mismatch.
- Summary at the bottom.

Exit code: 0 if all reported cleanly (regardless of current/needs-bump); 1 if any adopter wrapper was unreachable / unparseable.

### Step 2 — Emit suggested commands (if any need bumping)

```bash
scripts/operator/scp-wrapper-bump-sweep.sh --emit-commands
```

Adds a per-adopter command block at the end of the report. Each block is a copy-paste sequence:

1. `cd ~/Projects/<adopter>`
2. fresh branch off main
3. `sed -E` to bump BOTH the `@<SHA>` pin AND the `scp-sha:` input (axis-I requires they match)
4. commit + push
5. `gh pr create` with a routine commit message + PR body

The operator inspects, runs the blocks they want, and merges the PRs at leisure.

### Step 3 — Verify post-merge

After each adopter's bump PR merges:

- The `policy-check / scp/policy-check` required-check on that adopter's next PR exercises the new SCP HEAD.
- Bake observation criterion 2 (`≥1 SHA bump cycle merged + observed clean`) advances for that adopter — operator-attended bumps count.

---

## Adopter list maintenance

The script's `ADOPTERS=( … )` array is the source of truth. Update it when:

- **A new adopter is onboarded.** Append `"<owner>/<repo>"` to the array. (After the next cohort cascade slice, e.g. shopify-app post-024F.)
- **An adopter is decommissioned or paused.** Remove or comment out the entry.

Today's entries (2026-05-29): `jrnb2024/mapp-pim`, `jrnb2024/control-tower`, `jrnb2024/mapp-doc-agent`. Recommender is DEFERRED on `ErrManifestStale`; shopify-app is queued post-024F.

---

## What the script does NOT do

- It does NOT mutate any adopter repo automatically. The operator runs the emitted commands. This is intentional: no surprise PRs, no token-permission widening, no cross-repo CI to maintain.
- It does NOT clone repos locally. Everything is via `gh api`. (The emitted commands DO assume local clones at `~/Projects/<adopter>` — fix the path if your local layout differs, or run the bumps via `gh api repos/<adopter>/contents/<path>` PUT calls instead.)
- It does NOT cut an SCP release. Bumping to main HEAD is the canonical behaviour; for release-tag bumps, re-tag in SCP first, then run the sweep (it'll pick up the new HEAD).

---

## Reference

- **BACKLOG closure:** `FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001` — option (c) ratified 2026-05-29.
- **Companion script:** `scripts/operator/scp-wrapper-bump-sweep.sh`.
- **Axis-I invariant:** `docs/decisions/D-050-tf-pim-001-app-credential-surface-2026-05-21.md` (`@<SHA>` pin + `scp-sha:` input MUST match; ASC-2026-05-22-001).
- **Scaffolder template:** `templates/adopter-wrapper.yml.tmpl` — Renovate marker REMOVED 2026-05-29.
- **Revisit triggers:** estate exceeds 8-10 adopters OR monthly cadence misses 2+ adopters in a quarter → reconsider Renovate App self-host or Dependabot per-repo.
