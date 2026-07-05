# audit-changed cross-repo — Review Findings

```scp-review-evidence
{
  "review_id": "R1-AUDIT-CHANGED-CROSS-REPO",
  "area_id": "scp-audit-cross-repo-src",
  "reviewed_at": "2026-07-05T00:00:00Z",
  "summary": "3-lens adversarial review (correctness / safety_bypass / completeness_governance) of the cross-repo audit_changed + applies_to glob-tier change; all in-PR findings fixed, dispositions recorded.",
  "reviewed_paths": [
    "src/standards_control_plane/applies_to.py",
    "src/standards_control_plane/changed_audit.py",
    "src/standards_control_plane/cli.py",
    "src/standards_control_plane/audit.py",
    "src/standards_control_plane/review_evidence.py",
    "src/standards_control_plane/resources.py",
    "src/standards_control_plane/mcp_server/tools.py",
    "src/standards_control_plane/mcp_server/resources.py"
  ],
  "findings": [
    {
      "finding_id": "RV-ACXR-001",
      "status": "resolved",
      "summary": "review_evidence path resolution missed by repo-root threading (HIGH); fixed via audit_repo_root fallback with RED/GREEN regression test.",
      "domain": "governance"
    },
    {
      "finding_id": "RV-ACXR-002",
      "status": "resolved",
      "summary": "area_hint absent from audit cache key and external-worktree results cached across working-tree edits; both fixed (key extended, external roots uncached).",
      "domain": "architecture"
    },
    {
      "finding_id": "RV-ACXR-003",
      "status": "resolved",
      "summary": "CLI --repo-root accepted non-root directories and --write-output could co-mingle foreign findings into SCP stores; both refused with exit 2.",
      "domain": "governance"
    }
  ]
}
```

Full lens-by-lens dispositions: [r1-dispositions.md](r1-dispositions.md).
