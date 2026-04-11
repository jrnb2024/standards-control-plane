# Standards Control Plane — Returns Review

**Status:** live audit
**Generated at:** 2026-04-11T00:00:00Z
<!-- open-findings-signature: 2b3e3985acd7aeb7 -->
<!-- history-findings-signature: 27eef6301b182fab -->
**Scope:** subsystem `returns`, area `returns-exceptions`, paths `fixtures/returns-pilot`
**Standards version:** 2026-04-11

## Domain Scores
- governance: 100
- architecture: 25

## Top Open High-Severity Issues
- `F-ARCH-001-returns-exceptions` (ARCH-001) Code crosses bounded service roots: 1 file(s) reach directly across frontend/backend boundaries: fixtures/returns-pilot/frontend/app/exceptions/page.tsx
  - evidence: fixtures/returns-pilot/frontend/app/exceptions/page.tsx
- `F-ARCH-002-returns-exceptions` (ARCH-002) UI layer contains multi-step workflow orchestration: 1 UI file(s) coordinate workflow logic through backend imports or multiple awaited branches: fixtures/returns-pilot/frontend/app/exceptions/page.tsx
  - evidence: fixtures/returns-pilot/frontend/app/exceptions/page.tsx

## Recommended Next Actions
- Route cross-boundary work through the approved integration seam instead of importing bounded implementation modules directly.
- Move workflow orchestration into an action or service layer and keep UI modules focused on state binding.
- Move remote-access setup behind the approved service abstraction for the subsystem.

## Regressions
- none in this phase

## Notable Improvements
- `F-2026-00031` (ARCH-002) UI layer contains workflow orchestration: The returns exceptions page already mixes workflow branching into the UI layer and should not absorb more orchestration.
  - evidence: fixtures/returns-pilot/frontend/app/exceptions/page.tsx
- `F-2026-00033` (GOV-003) Returns work package evidence is incomplete: Recent returns work has missing review evidence files, so new changes in the same area should preserve a clear evidence trail.
  - evidence: fixtures/returns-pilot/docs/reviews/WP-RET-014/review_findings.md
