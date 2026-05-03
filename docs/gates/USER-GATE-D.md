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

- [ ] **(i) ≥3 estate adopters opted in, with FLA mandatory.** Verified by reading `docs/scorecards/opt-in-registry.yaml` — at least 3 entries; FLA entry is **required** as the named canary (per WP-SCP-023 plan-doc §8 Threshold A criterion + §10 Q6); the satisfied set is `FLA + ≥2 of {PIM / recommender / mapp-doc-agent / control-tower}`. **Note (TF-023E-001):** SCP-self CANNOT count toward this set while `standards-control-plane-` remains user-owned + private — GitHub blocks `actions/attest-build-provenance` on user-owned private repos with HTTP error "Feature not available for user-owned private repositories", so a self-emit cannot carry the OIDC attestation D-042 requires. SCP-self is added to the set only after the repo becomes public OR transfers to an org. Closes 023E R1 CMP-MAJ-003 + 023E fix-round-3 TF-023E-001 carve-out.
- [ ] **(ii) ≥1 weekly aggregator run committed cleanly.** Verified by reading `output/scorecards/index.json` — `aggregator_run_id` ≠ 0; `aggregated_at` is recent; ≥1 row has `status: verified`. The aggregator ran without infrastructure errors.
- [ ] **(iii) Markdown report rendered.** Verified by `ls docs/scorecards/*.md` — at least one weekly report file exists with content beyond the placeholder.
- [ ] **(iv) MCP method live.** Verified by querying the deployed MCP server at `acc.brokapps.ai`: `scp.consult_scorecard` returns aggregated metrics for at least one adopter. (Requires TF-023D-005 — MCP server redeploy on acc.brokapps.ai — to have completed.)
- [ ] **(v) CODEOWNERS coverage confirmed.** `docs/scorecards/**` + `output/scorecards/**` + `docs/security/mcp-signing-keys.pub` (via `docs/security/**`) + `.github/workflows/scorecard-aggregator.yml` (via `.github/**`) + `schemas/scorecard-*.schema.json` (via `schemas/**`).
- [ ] **(vi) TF-023D-003 closed (code AND operational).** Code: `_log_tool_invocation` reads the active key_id from `docs/security/mcp-signing-keys.pub` via `_resolve_audit_key_id()` (closed at slice 023E). **Operational:** `docs/security/mcp-signing-keys.pub` actually contains an active key entry. Currently empty (comment-only) — until the operator generates + commits a key, audit attribution falls back to the `key-ring-unreadable` sentinel. Both code AND operational must be satisfied to check this box. Closes 023E R1 nit-SAFE-001.
- [x] **(vii) Cross-repo notification sent.** `~/Projects/control-tower/governance/docs/notifications/SCP-SCORECARD-SURFACE-LIVE-2026-05-03.md` — landed at slice 023E (closes TF-023A-002).
- [ ] **(viii) Forward-filed TFs are in healthy state.** TF-023A-001/002, TF-023D-001/002/004/005, **TF-023E-001** (SCP-self opt-in deferred until repo public/org-owned), **TF-023E-002** (restructure policy-check.yml so attest-scorecard is a separate top-level workflow — wrapper SHA pin stuck at v1.0.0 until then) all named in STATUS.md with closure paths.

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
