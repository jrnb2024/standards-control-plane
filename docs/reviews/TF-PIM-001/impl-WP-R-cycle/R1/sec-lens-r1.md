# TF-PIM-001 impl WP — sec lens R1 review (v0.2)

**Dispatched:** 2026-05-21 PM against impl WP plan-doc v0.2 at `ef5312e`
**Agent type:** Plan (read-only; DO-NOT-EDIT mandate per `feedback_subagent_review_only_scope_must_be_enforced`; sample-size-3: CT c565fd0 / Recommender V14 INT #2 / docs/ESTATE-CONVERGENCE.md)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens precedent:** reuse pattern from `docs/reviews/TF-PIM-001/shortlist-A-C-D/sec-lens-r1.md`

---

## Lens: sec — TF-PIM-001 impl WP v0.2 R1 review

### Verdict
ACCEPT-WITH-AMENDMENT

### Summary

v0.2 materially strengthens the impl plan-doc relative to v0.1 across the highest-risk surfaces. The 4-step `.pem` discipline in Wave A (steps 0a/0b/7/8 with the explicit macOS `srm -P` callout) directly addresses all three canonical attack surfaces identified in the path-ratification review. The fallback action selection decision rule is explicit about what constitutes a "documented blocker." The Wave D YAML sketch correctly preserves `persist-credentials: false` on both cross-repo checkout steps. TF-PIM-001-SEC-001 through 005 are all mapped to waves in the §3.3 inherited-TF table with no orphaned items. D-050 ADR scope in Wave B captures the five load-bearing sec elements (App credential scope, §12.7.10 invariant preservation rationale, key-custody posture, reversal mechanism, cross-references). On balance, the sec posture of v0.2 is stronger than the path-ratification baseline at every point the prior review raised.

Three findings require amendment before v0.3 dispatch. Two are MIN: (1) the `gh api .../actions/secrets` audit command at Wave A step 7 is subject to GitHub's default 30-item pagination — on a repo with more than 30 secrets the command silently returns an incomplete list, and the `grep` may never match the two new secret names even if they were uploaded correctly; a `--paginate` flag or explicit page-size override is needed; (2) the §6.4 verify command `gh search code --owner=jrnb2024 'secrets: inherit'` does not search private repositories under `@jrnb2024` by default in all GitHub CLI versions — the `gh search code` subcommand operates against the GitHub code-search API which, for authenticated users, does cover private repos they have access to, but the plan-doc's comment "Expect: zero matches in adopter policy-check-wrapper.yml files" over-states coverage without confirming the private-repo inclusion. One finding is NIT: the Wave A rotation SOP cross-reference says "rotation SOP authored here" in §3.2 (out-of-scope deferred row) and claims "Rotation SOP authored in Wave A + Wave C" in §7.3, but Wave A's Actions list contains no step authoring or filing the rotation SOP document — the SOP exists as a TF item (TF-PIM-001-SEC-001 mapped to Wave A + Wave C) but Wave A's discrete actions don't include a step writing or linking to the rotation SOP file. This gap means the SOP could be silently dropped unless Wave C explicitly picks it up with a named deliverable.

No findings rise to MAJ. The two MIN findings are both remediable in a targeted v0.3 amend (one line each). The NIT is a small scope-clarification in Wave A's action list.

### Findings

**SEC-MIN-001 — Wave A step 7 + §7.1 mitigation: `gh api .../actions/secrets` needs `--paginate` flag**

- **Section:** §5 Wave A step 7; §7.1 mitigation bullet "Step 7 — Post-upload audit"
- **Description:** The audit command `gh api repos/jrnb2024/standards-control-plane/actions/secrets --jq '.secrets[].name' | grep -E "SCP_FEDERATION_APP_(ID|PRIVATE_KEY)"` is paginated by the GitHub REST API at 30 items per page by default. The Actions Secrets API endpoint (`GET /repos/{owner}/{repo}/actions/secrets`) wraps results in a `{"total_count":N, "secrets":[...]}` envelope and returns at most 30 items per page unless `?per_page=100` is specified. The `.secrets[].name` jq expression extracts only from the first page. On a repo with more than 30 existing secrets, both new secrets could exist on page 2 and the `grep` would silently return no matches.
- **Proposed remediation:** Replace step 7 command with `gh api --paginate repos/jrnb2024/standards-control-plane/actions/secrets --jq '.secrets[].name' | grep -E "SCP_FEDERATION_APP_(ID|PRIVATE_KEY)"`. Update the matching §7.1 bullet identically.
- **Severity-rationale:** MIN rather than MAJ because the false-negative scenario requires 30+ secrets accumulated. But: a step 7 false-negative means the operator could proceed to step 8 (`shred -u`) believing the upload succeeded when it did not, irrecoverably destroying the only copy of the private key. That downstream consequence elevates this above NIT.

**SEC-MIN-002 — §6.4 §12.7.10 invariant verification: `gh search code` has indexing lag + auth-scope caveat**

- **Section:** §6.4 §12.7.10 invariant preservation (cross-cutting)
- **Description:** `gh search code --owner=jrnb2024 'secrets: inherit'` uses GitHub Code Search API which does index private repos to which the authenticated identity has access (requires `repo` scope in the token), BUT has a known indexing lag (typically minutes to hours after a commit, occasionally longer). A recently added `secrets: inherit` in an adopter wrapper would not appear in search results during the lag window. More concretely: the comment "Expect: zero matches in adopter policy-check-wrapper.yml files" does not distinguish between "no adopter ever added `secrets: inherit`" and "search index has not yet ingested a recent commit that added it." This is not theoretical — it is the exact scenario the verification step is supposed to catch (a Codex-dispatched Wave D touching workflow files and accidentally adding `secrets: inherit` in the same PR).
- **Proposed remediation:** Augment §6.4 to note (a) the required authentication scope for `gh search code` to cover private repos (`GITHUB_TOKEN` or PAT with `repo` scope); (b) the indexing lag caveat and a secondary local grep verification for the Wave D fix PR specifically — `grep -r 'secrets:.*inherit' .github/workflows/` in the SCP repo checkout to confirm no `secrets: inherit` was introduced.
- **Severity-rationale:** MIN — the §12.7.10 invariant is load-bearing but the verification-completeness gap is closable; the Wave D R1 review (§5.2) is the primary enforcement gate.

**SEC-NIT-001 — Wave A Actions list missing SOP-authoring step**

- **Section:** §5 Wave A actions list; §3.2 out-of-scope row; §7.3 mitigation; §9 follow-ups
- **Description:** TF-PIM-001-SEC-001 maps in §3.3 to "Wave A + Wave C (docs)". §7.3 states "Rotation SOP authored in Wave A + Wave C." But Wave A's Actions list (steps 0a, 0b, 1-9) contains no discrete step that authors or files the rotation SOP document. Without a named Wave A action step, the SOP could be silently dropped — Wave C's ADOPT-001 updates reference the rotation SOP without authoring it.
- **Proposed remediation:** Add a step 10 to Wave A's Actions list: "10. Author App-key rotation SOP — committed as a documentation file (e.g., `docs/security/app-key-rotation-sop.md`) capturing the 5 content items from TF-PIM-001-SEC-001."
- **Severity-rationale:** NIT — deliverable-traceability gap; SOP content is fully specified upstream.

### Strengthening since path-ratification R1

1. `.pem` discipline operationalised end-to-end with macOS `srm -P` callout (exceeds TF-PIM-001-SEC-001)
2. Fallback decision rule named + criterion-bounded (tighter than TF-PIM-001-SEC-003)
3. D-050 ADR scope explicitly captures §12.7.10 invariant preservation rationale (closes Decision point 4 "partially resolved" flag)
4. Wave G failure tree + Wave D rollback strategy are new + sec-load-bearing
5. TF-PIM-001-SEC-004 per-adopter App-install access verification scoped correctly (PIM canary; cohort deferred)

### Carry-forward to R2

1. SEC-MIN-001 closure confirmation: `--paginate` present in both Wave A step 7 and §7.1 bullet
2. SEC-MIN-002 §6.4 augmentation: local grep + auth-scope callout AND Wave D R-cycle protocol (§5.2) also references local grep
3. SEC-NIT-001 Wave A step 10 addition + verification block updated
4. (R2-eligible carry) App scope at GitHub UI — post-Wave A verification could add `gh api /apps/scp-federation-primitive --jq '{permissions, installation_policy}'` to catch misclick during UI ceremony; below SEC-MIN threshold for v0.2 R1 but worth flagging

### Convergence signal
ITERATE-EXPECTED — verdict ACCEPT-WITH-AMENDMENT; SEC-MIN-001 + SEC-MIN-002 + SEC-NIT-001 fold into v0.3; R2 expected against the amended plan-doc.
