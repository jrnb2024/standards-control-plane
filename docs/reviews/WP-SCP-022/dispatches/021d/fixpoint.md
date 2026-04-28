# Slice 021D — fixpoint record

**Slice:** WP-SCP-022 / WP-SCP-021 §4 021D (MCP resources + domain-map + signing-keys)
**Date:** 2026-04-28
**Round count:** 5 (R1 → fr1 → R2 → fr2 → R3 → fr3 → R4 → fr4 → R5 → fixpoint)
**Fix-round budget:** 4 used of 5 (last fix-round in budget; fr3 had Codex-timeout false-closure caught at R3 and re-applied by orchestrator)

R5 verdicts (all-three APPROVED_WITH_FINDINGS, MIN/nit only):
- correctness: 2 MIN
- safety_bypass: 1 MIN
- completeness_governance: 4 MIN + 1 nit

**Fixpoint per WP-SCP-022 §4.3.**

Trajectory: R1 (11 MAJ) → fr1 → R2 (5 MAJ) → fr2 → R3 (5 MAJ — false-closure detected) → fr3 (orchestrator-applied) → R4 (1 MAJ — narrow except) → fr4 (broaden except) → R5 fixpoint.

Real bugs caught + closed: snapshot time-of-check race; per-id URI state-handling for expired waivers/closed decisions; D-NNN regex 3-digit limit (recurring bug); waivers.json scanning under findings; signing-keys outage isolation; MITM-bypassable trust-model wording; U-21-* unknown closure docs; server.py instructions stale; broader exception class for git timeout/missing.

## sha256_chain
correctness: f874b11ad020834d4050fe06063e193b59d8767df8a49a05ef68848d2c7b3a57
safety: e6b0948177879a631bab4c7de11a8c4c63947be751b6f0fdc5341258ec6ef748
completeness: 3765d3ff36a498fd80f7db47720d78fdd776f38fd5a56ad8bcfe437322db10c3
chain: 5a57a4a226c1edcee548e201cb51e8d7a2268c203161265b7fb8a6c179823f0f
