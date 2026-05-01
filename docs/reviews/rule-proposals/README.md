# SCP Rule Proposals — RFC-lite Process

**Status:** active as of slice 020H.1 (2026-05-01).
**Closes:** WP-SCP-020 §4 020H.1 sub-criterion (iii) — closure of BS-5
governance ask.

---

## When to file a rule proposal

File a `RULE-NNN.md` proposal in this directory when:

- You want to **add a new `SCP-R-NNN` rule** to the federation primitive's
  starter library.
- You want to **promote an existing rule** from `threshold: warn` to
  `threshold: deny` as the SCP-source default. (Adopter-side overrides via
  `.scp/rule-config.yaml` do NOT need a proposal — they're a per-repo
  governance decision.)
- You want to **propose a breaking change** to an existing rule's match
  scope or shape that would require a MAJOR bump per
  `policies/VERSIONING.md`.
- You want to **deprecate or remove** an existing rule.

You do NOT need a proposal for:

- Bug fixes to an existing rule (PATCH bump — direct PR is fine).
- Performance improvements or refactors to rule internals.
- New informational annotations on existing rules.
- Tightening Rego style or fixing lint issues.

---

## Process

### 1. Draft the proposal

Copy `RULE-TEMPLATE.md` to `RULE-NNN.md` (next sequential `NNN` after
the highest existing). Fill in every section. Open a PR adding the file
to this directory.

The PR may also include a **proof-of-concept implementation** as a
companion patch in `policies/<rule-id>.rego` + `policies/tests/`, but
the implementation MUST be marked **draft** in the proposal — it is
illustrative, not the merge target.

### 2. Review window

- **Quorum:** ONE approval from a `SCP-CODEOWNERS` member is sufficient
  to accept. A single approval represents quorum because (a) the SCP
  estate is single-operator at v1.0.0 (per D-031 in `docs/DECISIONS.md`,
  with bus-factor-1 escalation review at 2026-07-21), and (b) downstream
  adopters retain per-repo `.scp/rule-config.yaml` opt-in / opt-out for
  any new rule.
- **Bypass-introducing proposals — non-waivable 48h window.** When the
  proposal's §5 "Bypass surface" is non-empty (any new
  `.scp/rule-config.yaml` key, any new `scp_bypass: <variant>` flag,
  any new per-finding waiver shape, OR any §5 implicit-exclusion set
  that wasn't named in a prior proposal), the 48h window is
  **non-waivable** — the author MUST NOT extend, and the
  proposal MUST include an explicit "Bypass surface enumeration"
  paragraph in the PR description that names every adopter-side
  control governing the surface. This prevents a same-day rush of a
  bypass-introducing proposal and surfaces the bypass for adversarial
  review during the window. Closure of WP-SCP-022 020H.1 R1
  SAFE-MAJ-001.
- **Window (non-bypass proposals):** **48 hours wall-clock** from PR
  open (weekends count; the estate operates seven days a week per the
  four-tier dispatch pattern). The author may extend the window if the
  proposal is substantial — note the extension in the PR description.
- **Zero approvals at window close → auto-defer to next cycle.**
  The PR is closed without merge; the author may re-open it or revise
  and re-file as a new proposal at any later point. A `defer` label
  is applied so the auto-defer event is searchable. Closure of BS-5.

When a second maintainer onboards (per D-031 escalation path), the
quorum threshold flips to **2 of N** with `require_review_from_non_author`
as the GitHub-enforcement mechanism. That change is a one-line edit to
this file and a branch-protection update.

### 3. Merge

A merged proposal becomes the **canonical specification** for the rule
addition / change. The implementation lands as a separate PR (or via
amendments to the same PR if PoC code was included) with the
`scp-rule-proposal` Renovate label removed and the rule live.

The merged proposal is referenced by:

- The rule's Rego header comment (`# RULE: SCP-R-NNN — see docs/reviews/rule-proposals/RULE-NNN.md`).
- The release notes for the version that ships the rule.
- An entry in `docs/DECISIONS.md` if the rule introduces a new domain
  or escalates an existing rule's threshold (e.g. promoting `warn` →
  `deny` default).

### 4. After merge — adoption track

Per `policies/VERSIONING.md`:

- **New rule at `threshold: warn`:** lands in the next MINOR release.
  Adopters see the rule fire as a warning annotation on PRs that
  match its conditions but the merge is not blocked. Adopters opt
  into deny via their own `.scp/rule-config.yaml`.
- **Promoting to `threshold: deny` default:** lands in the MAJOR
  after the deprecation ramp's notice window. Migration pointer in
  the rule's pre-promotion `::warning::` annotation directs adopters
  here.
- **Breaking change to existing rule:** follows the deprecation ramp
  in `policies/VERSIONING.md`.

---

## Authorship guidance

- **Each proposal documents WHY first**, not WHAT. Adopters reading
  the proposal need to understand the threat model or governance
  concern that motivates the rule before they evaluate the
  implementation.
- **Cite a real-world finding** that motivated the rule. A rule that
  exists only because it could exist is harder to defend against
  in an adopter's adversarial review than a rule that closes a known
  gap in a known system.
- **Show the false-positive surface**. Every rule has one. Naming the
  cases where the rule will fire on legitimate manifests is part of
  the proposal — adopters need this to decide whether to opt in.
- **Show the bypass-surface**. A rule that adds a new bypass surface
  (e.g. a new `.scp/rule-config.yaml` key, a new `scp_bypass` flag)
  must surface that explicitly so the bypass is part of the review.

---

## Auto-defer mechanics

When a proposal PR exceeds the 48h window with zero approvals:

1. A maintainer (or a future auto-defer GitHub Action) closes the PR
   with the `defer` label and a comment naming the next review cycle.
2. The PR's diff remains visible in the closed-PR list; nothing is
   destructive.
3. The author may revise and re-file at any time — there is no
   blacklist on re-proposals. The 48h window restarts on re-open.

This is intentionally lightweight at v1.0.0 because the SCP estate
is single-operator. As estate scale grows (WP-SCP-024 cascade), the
auto-defer mechanism may be lifted to a GitHub Action that runs on a
schedule and applies the label automatically.

---

## References

- `policies/VERSIONING.md` — semver contract.
- `RULE-TEMPLATE.md` (in this directory) — copy-paste starter.
- WP-SCP-020 plan §4 020H.1 (iii) — slice acceptance for this process.
- `docs/DECISIONS.md` D-022 — federation-primitive adoption (referenced
  for the BS-5 closure rationale).
- ADOPT-001 §12.7 — adopter integration appendix.
