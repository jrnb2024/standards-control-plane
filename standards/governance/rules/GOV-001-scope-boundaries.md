# GOV-001 — Scope Boundaries Must Be Explicit

**Domain:** governance  
**Version:** 1.0.0  
**Status:** active  
**Severity default:** high

Implementation work must identify the intended scope boundary before coding
starts, including the target subsystem, affected files or areas, and any
out-of-scope concerns that should be flagged rather than silently absorbed.

## Signals

- no declared subsystem or work area
- changes spread into unrelated files without justification
- implicit scope changes appear only in implementation notes or diffs

## Rationale

Silent scope expansion is one of the most common ways governance drift enters a
repo and one of the easiest failure modes for implementation agents.
