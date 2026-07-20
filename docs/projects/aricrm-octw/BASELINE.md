# AriCRM + OCTW Adaptation — Baseline Manifest

## Status

Incomplete — not approval evidence. This manifest records reproducible inputs and
validation results gathered on 2026-07-19. It cannot close GOV-002 while the AriCRM
working tree is dirty and the pinned OpenClaw image has not passed the required runtime
validation.

## Source identities

| Component | Repository/branch | Commit or digest | Evidence |
|---|---|---|---|
| OCTW fork | `https://github.com/myseocompany/OCTW`, `codex/document-aricrm-octw-project` | `f23d32b80a66b155b0e641526417d04412843a32` | `git rev-parse HEAD` |
| OCTW source audited | `https://github.com/myseocompany/OCTW`, `main` | `299c33b368c579db62339ccdccc51e53bca5345c` | Static audit evidence in `STATUS.md` |
| OCTW upstream comparison | `https://github.com/kumanday/OCTW`, `upstream/main` | `299c33b368c579db62339ccdccc51e53bca5345c` | `git fetch upstream && git log upstream/main -1` |
| AriCRM integration candidate | `https://github.com/myseocompany/aricrm.git`, `main` | `4b5539c72cf0a7cab93e7df0ac5920237255bdfd` | `git -C ../aricrm rev-parse HEAD`; working tree has 121 changed/untracked paths, so this is not an audit-approved source baseline |
| OpenClaw | `ghcr.io/openclaw/openclaw` | `2026.7.1`; `ghcr.io/openclaw/openclaw@sha256:6a31d44b2944e7adcd2b582bf6fb463111264ebca97a0201795b799135bd102c` | OCI labels and `docker buildx imagetools inspect` |

The OpenClaw image index resolves to Linux AMD64 manifest
`sha256:165b4992f1b4b74ffdd7a02c887ba006f9f5dc951eca420eef573a8b233b543f`
and Linux ARM64 manifest
`sha256:38b611f494cb32e15aaf456d54c6b6be55db9098c90632aed0bfad4a70009707`.
Its OCI source revision is `2d2ddc43d0dcf71f31283d780f9fe9ff4cc04fe4`.

## Environment

| Tool | Version |
|---|---|
| Git | `2.39.5 (Apple Git-154)` |
| Python | `3.14.5` |
| Docker CLI | `29.4.0`, build `9d7ad9f` |
| Docker Compose | `v5.1.2` |

Reviewer: Codex. Environment: local macOS development workspace with OrbStack Docker
daemon; Docker client/server version `29.4.0`.

## Commands and results

| Command | Result |
|---|---|
| `git fetch upstream && git log upstream/main -1` | Passed; upstream SHA equals the audited OCTW SHA. |
| `python3 -m compileall -q src tests` | Passed. |
| `docker compose config -q` | Passed, with a warning that `OCTW_KEK` was unset and defaulted to an empty string. |
| `docker buildx imagetools inspect ghcr.io/openclaw/openclaw:latest` | Passed; resolved the immutable OpenClaw index digest above. |
| OCI configuration-label inspection for the AMD64 manifest | Passed; recorded OpenClaw version and source revision above. |
| `docker pull ghcr.io/openclaw/openclaw@sha256:6a31d44b2944e7adcd2b582bf6fb463111264ebca97a0201795b799135bd102c` | Passed through OrbStack. |
| `docker run --rm --entrypoint openclaw ghcr.io/openclaw/openclaw@sha256:6a31d44b2944e7adcd2b582bf6fb463111264ebca97a0201795b799135bd102c --version` | Passed; returned `OpenClaw 2026.7.1`. |

## Limitations and closure requirements

- AriCRM must be reviewed at a clean, committed SHA; then update this manifest with the
  exact reviewed revision and reviewer evidence.
- OCTW defaults now pin this image; run Docker/OpenClaw lifecycle and compatibility
  tests before treating it as supported for production.
- `uv` and `pytest` are unavailable in this environment; the automated suite was not
  executed. The new configuration-default assertion also could not run because
  `pydantic_settings` is not installed in the active Python environment.
- Record the exact committed document revision reviewed for approval or re-audit.

This manifest supports `SPEC.md` §14 and does not change the no-go recommendation in
`STATUS.md`.
