# USER-GATE-D — WP-SCP-023 Threshold A signoff

**Status:** `not-yet-signed` — scaffolded at slice 023E for operator sign-off when criteria are satisfied.
**Date scaffolded:** 2026-05-03 (WP-SCP-023 023E)
**Date signed:** _(pending)_
**Operator:** _(pending — @jrnb2024)_

## Purpose

WP-SCP-023 (cross-repo scorecards) reaches **Threshold A** when the cross-repo aggregator surface is operationally trusted across the estate, demonstrated by ≥3 adopters opted in + ≥1 weekly aggregator run cleanly producing a verified index + the markdown report + MCP method live and queryable.

This artefact ratifies that the operator has reviewed the criteria + signed off on closing WP-SCP-023.

## Threshold A criteria

Each criterion below MUST be satisfied before signing.

- [ ] **(i) ≥3 estate adopters opted in.** Verified by reading `docs/scorecards/opt-in-registry.yaml` — at least 3 entries; SCP-self counts as 1, so ≥2 of {FLA / PIM / recommender / mapp-doc-agent / control-tower} also need entries.
- [ ] **(ii) ≥1 weekly aggregator run committed cleanly.** Verified by reading `output/scorecards/index.json` — `aggregator_run_id` ≠ 0; `aggregated_at` is recent; ≥1 row has `status: verified`. The aggregator ran without infrastructure errors.
- [ ] **(iii) Markdown report rendered.** Verified by `ls docs/scorecards/*.md` — at least one weekly report file exists with content beyond the placeholder.
- [ ] **(iv) MCP method live.** Verified by querying the deployed MCP server at `acc.brokapps.ai`: `scp.consult_scorecard` returns aggregated metrics for at least one adopter. (Requires TF-023D-005 — MCP server redeploy on acc.brokapps.ai — to have completed.)
- [ ] **(v) CODEOWNERS coverage confirmed.** `docs/scorecards/**` + `output/scorecards/**` + `docs/security/mcp-signing-keys.pub` (via `docs/security/**`) + `.github/workflows/scorecard-aggregator.yml` (via `.github/**`) + `schemas/scorecard-*.schema.json` (via `schemas/**`).
- [ ] **(vi) TF-023D-003 closed.** `_log_tool_invocation` reads the active key_id from `docs/security/mcp-signing-keys.pub` (replaced `pending_021J` placeholder).
- [ ] **(vii) Cross-repo notification sent.** `~/Projects/control-tower/governance/docs/notifications/` carries the v1.2.0 + scorecards announcement.
- [ ] **(viii) Forward-filed TFs are in healthy state.** TF-023A-001/002, TF-023D-001/002/004/005 all named in STATUS.md with closure paths.

## Operator sign-off

Once all criteria above are checked, fill in the date + sign below to close WP-SCP-023.

```
Date: ____________________
Signed: __________________  (@jrnb2024)
Notes: ___________________
```

## Post-signoff actions

After this artefact is signed:

1. Mark **WP-SCP-023 ✅ closed** in STATUS.md "At-a-glance" + "## Threshold A" section.
2. Update memory `project_post_threshold_a_state.md` to reflect WP-SCP-023 closure.
3. Update memory `project_wp_scp_023_state.md` to "Closed at Threshold A on <date>" (similar to WP-SCP-019/020/021/022 close-out language).
4. Cut **v1.3.0** if any new MINOR additions accumulated; otherwise no version bump.
5. Move to next-substantive WP (WP-SCP-024 estate cascade per the 5-move-MVCP successor).

## References

- `docs/plans/WP-SCP-023-cross-repo-scorecards.md` — full plan-doc.
- `docs/DECISIONS.md` D-041 / D-042 / D-043.
- WP-SCP-022 §USER-GATE-A pattern — analogous Threshold A artefact for the federation primitive.
- `docs/reviews/WP-SCP-023/dispatches/023E-threshold/DISPATCH-NOTE.md`.
