# 021b Fix Round 1 Notes

- The evidence package now probes `tests/scp_mcp/test_cli_help.py` explicitly in both 021b dispatch packages so AC4a is visible to future reviewers.
- The original 021b dispatch package now includes `.gitignore` in `scope_boundary` to reflect the branch state reviewed for this slice.
- The current `.gitignore` update keeps MCP signing-key artefacts and editable-install metadata out of tracked history.
