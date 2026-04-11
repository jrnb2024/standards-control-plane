# ARCH-002 — UI Layer Must Not Own Domain Orchestration

**Domain:** architecture  
**Version:** 1.0.0  
**Status:** active  
**Severity default:** high

Presentation components should not become the place where multi-step business
workflow, data branching, or orchestration logic accumulates.

## Signals

- multiple API calls coordinated inside a page component
- business branching embedded in rendering code
- direct repository or database access from UI modules
