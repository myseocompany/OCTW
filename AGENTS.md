# Repository Agent Instructions

## GitHub authentication in the managed sandbox

- `gh auth status` can report an invalid token when executed inside the restricted sandbox even though the keyring session is valid.
- Before asking the user to run `gh auth login`, rerun `gh auth status` with escalated permissions outside the sandbox.
- Ask the user to authenticate only when the escalated check also fails.
- Never print or persist the full GitHub token.
- Git metadata may be read-only inside the sandbox, so branch creation, staging, and commits may also require the normal escalation flow.

## Commit scope

- Stage only files that belong to the requested change.
- Do not include `.DS_Store` or unrelated files under `docs/projects/`.
