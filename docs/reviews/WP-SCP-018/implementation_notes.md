# WP-SCP-018 Implementation Notes

## Implementation summary

- added optional bearer-token protection for `GET /registry`, `POST /consult`,
  and `POST /audit`, while keeping `GET /health` public
- extended `serve` with `--auth-token`
- added `estate_reporting.py` plus:
  - multi-repo dashboard output
  - persisted portfolio history
  - persisted trend view against prior snapshots
  - `estate-report` CLI command
- extended project-area artefacts with:
  - `storybook_metadata`
  - `screenshots`
  - `graphs`
- widened path classification so repo-root scopes and nested scopes behave the
  same way for docs, prompts, review evidence, tests, frontend/backend tags,
  Storybook, screenshots, and graph artefacts
- updated README and sample output generation

## Review outcome

The main implementation correction was to stop assuming nested paths in the
normaliser. Without that fix, richer evidence classification would have looked
correct in the seeded fixtures but failed for real repo-root scopes.
