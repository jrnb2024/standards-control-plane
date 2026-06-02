<!-- not the adopter CLAUDE.md; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-030-claude-absent

WP-SCP-030 companion-activation selftest fixture — **row 3** of the SPEC §6 matrix
(opted-in, but the fixture-repo has **no** root `CLAUDE.md` → `::warning::`, gate green).

Proves the distinct `input.claude_md_present == false` materialisation branch: the
repo-level eval step must detect an ABSENT CLAUDE.md (not merely a marker-less one)
and fire the `claude_md_absent` finding. Like row 2 the rule is warn-baseline, so the
gate stays GREEN.

- `rule-config.yaml` — `acc-hook-installed: true`.
- `repo/` — intentionally contains NO `CLAUDE.md` (only this note placeholder, so the
  subtree is a non-empty, committable directory; `.md` is skipped by conftest).
- `expected-annotations.json` — one SCP-R-030 `claude_md_absent` deny finding; gate green.
