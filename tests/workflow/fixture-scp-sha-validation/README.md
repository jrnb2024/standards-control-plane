# fixture-scp-sha-validation

Selftest fixture for TF-PIM-001 Wave D'.1 axis I coverage.

The workflow-selftest harness drives five cases against this fixture:

1. `fixture-scp-sha-validation-happy-path-policy-check` passes `scp-sha: ${{ github.sha }}` and expects a green run.
2. `fixture-scp-sha-validation-required-input-missing-policy-check` passes `scp-sha: ""` with `simulate-cross-repo: true` and expects pre-flight SCP-E001 failure.
3. `fixture-scp-sha-validation-wrong-sha-shape-policy-check` passes `scp-sha: not-a-sha` and expects pre-flight SCP-E001 failure.
4. `fixture-scp-sha-validation-mismatched-valid-sha-policy-check` passes the all-zero SHA and expects downstream checkout failure after shape validation passes.
5. `fixture-scp-sha-validation-cross-repo-happy-path-policy-check` passes `scp-sha: ${{ github.sha }}` with `simulate-cross-repo: true` and expects a green run through the wrapper-bump simulation path.

`wrapper.yml` is a pre-authored local mirror of the adopter wrapper shape for the case-5 simulation. The workflow-selftest jobs still call `./.github/workflows/policy-check.yml` directly; the wrapper file exists as the canonical fixture artefact for the cross-repo shape.
