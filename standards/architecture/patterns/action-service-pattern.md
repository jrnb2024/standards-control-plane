# action-service-pattern

Use when UI actions trigger meaningful business workflow.

The pattern should bias toward:

- view emits intent
- action or service layer owns orchestration
- remote calls and branching live outside rendering code
- remediation and retry logic stay near the integration seam

