# AriCRM + OCTW Adaptation - CI, Branch Protection, and Release Plan

## Status

Approved as the Phase 0 CI policy. This document defines the required baseline; the
GitHub Actions workflow and branch protection rules still need to be implemented.

## Minimum GitHub Actions workflow

Create a required workflow named `ci.yml` for pull requests and pushes to `main`.

Required jobs:

- `compile`: install with `uv sync --frozen --all-groups`, then run
  `python -m compileall -q src tests`.
- `lint`: run `uv run ruff check .` and `uv run mypy src`.
- `test`: run `uv run pytest`.
- `compose-config`: run `docker compose config -q` with explicit non-production
  placeholder secrets set in the workflow environment.

Initial workflow policy:

- Fail closed on compile, lint, type-check, test, or Compose configuration errors.
- Upload pytest coverage output when available, but do not block on a coverage
  threshold until baseline coverage is measured.
- Keep the existing Codacy security scan as a separate security signal. It should not
  replace the required CI workflow above.

## Branch protection for `main`

Require:

- One approving review before merge.
- Required status checks: `compile`, `lint`, `test`, and `compose-config`.
- Branches to be up to date before merge.
- Conversation resolution before merge.
- No force-pushes.
- No branch deletion.
- Linear history or squash merge only.

Allow:

- Administrator bypass only for documented break-glass incidents.
- Draft pull requests for work in progress, but no merge until all required checks pass.

## Release strategy

Use SemVer tags: `vMAJOR.MINOR.PATCH`.

Minimum release steps:

- Merge to `main` only through protected pull requests.
- Update `CHANGELOG.md` with user-visible changes, security fixes, migration notes,
  dependency updates, and operational caveats.
- Tag the reviewed commit with a signed or GitHub-verified annotated tag.
- Build and publish artifacts only from the tag.
- Record the OCTW commit, OpenClaw image digest, migration revision, and AriCRM
  integration contract version in the release notes.

## Dependency updates

- Use scheduled dependency review weekly.
- Group routine Python dependency updates into one pull request.
- Keep security updates separate and prioritized.
- Require the full CI workflow before merging any dependency update.
- Re-resolve and record OpenClaw image digests explicitly; never follow mutable tags
  in production.

## Environment matrix

Initial CI matrix:

| Area | Values | Purpose |
|---|---|---|
| Python | `3.12`, `3.13` | Project minimum and near-current compatibility |
| OS | `ubuntu-latest` | Primary CI and Docker host target |
| Docker | GitHub-hosted Docker Engine | Compose config and Docker-facing tests |
| Compose | Installed GitHub Actions plugin | Match the production deployment workflow as closely as practical |

Deferred matrix expansion:

- macOS local validation is useful for OrbStack developer checks, but should not be a
  required production CI gate.
- Python `3.14` should be added only after dependencies and CI runners support it
  reliably.
- Docker lifecycle tests should run in a dedicated job once Phase 1 provides safe
  test fixtures and cleanup.
