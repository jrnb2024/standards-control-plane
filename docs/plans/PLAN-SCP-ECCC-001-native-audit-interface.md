# PLAN-SCP-ECCC-001 — Native audit interface closure

1. Add the bounded JSON contract and a focused conformance test.
2. Run the focused test and the existing SCP regression suite.
3. Complete three-lens adversarial review and close every finding.
4. Merge through PR, then pin the exact merged Git objects in ECCC-001C candidate A.

Acceptance: contract/parser/schema/result agreement is executable; no production code,
new endpoint, service, database, fixture-only behaviour or broad capability claim.
