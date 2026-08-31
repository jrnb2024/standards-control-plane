# PLAN-SCP-ECCC-001 — Native audit interface closure

1. Add the bounded JSON contract and a focused conformance test.
2. Constrain `scope.subsystem` in the request schema to
   `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`, and declare the same grammar in the
   native contract.
3. Prove malformed request exit 1, argparse misuse exit 2, traversal rejection
   without filesystem escape, read-only default behaviour, and isolated
   `--write-output` writer delegation.
4. Run the focused test and the existing SCP regression suite.
5. Complete three-lens adversarial review and close every finding.
6. Merge through PR, then pin the exact merged Git objects in ECCC-001C candidate A.

Acceptance: contract/parser/schema/result agreement is executable; unsafe subsystem
values cannot reach output path interpolation; default audit mode is persistence-free;
write-output delegation is tested without the repository's real output tree; no
production code, new endpoint, service, database, fixture-only behaviour or broad
capability claim.
