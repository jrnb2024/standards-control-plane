# ECCC-001C native audit — R1 safety

**Verdict:** APPROVE after fix

Initial P1: unconstrained `scope.subsystem` could traverse writer paths when
`--write-output` was selected. Closure: the request schema and contract enforce
`^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`; tests reject slash, backslash, dot segments,
whitespace and absolute paths and prove default no-write behaviour. No generated test
outputs remain.
