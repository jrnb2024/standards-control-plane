# --restore real-repo round-trip evidence (PLACEHOLDER)

**Status:** PLACEHOLDER - operator-interactive demo at dispatch-plan step 7 has NOT yet run. Merge-blocking AC per WP-SCP-024 plan-doc §6 + 024A R1 MAJ-SAFE-003.

**To close this placeholder:**
1. Operator creates a throw-away test repo (e.g. jrnb2024/scp-024b-extras-restore-test).
2. Configure adopter wrapper + run forward-mode enable-required-check.sh.
3. Capture pre-state JSON via the prior invocation log entry.
4. Mutate branch protection (e.g. via gh CLI) to known different state.
5. Run `--restore <pre-state.json>` mode.
6. Verify branch-protection API GET response matches captured before-state byte-for-byte (jq diff).
7. Replace this file's content with the demo log + diff output + operator sign-off + timestamp.

Tracked at TF-024B-STEP7-DEMO-001 (STATUS.md).
