# AriCRM + OCTW Adaptation — Baseline Manifest

## Status

Incomplete — not approval evidence. This manifest records reproducible inputs and
validation results gathered on 2026-07-19. AriCRM has been audited at a clean worktree,
but OpenClaw lifecycle compatibility evidence and the remaining baseline closure
evidence are still required.

## Source identities

| Component | Repository/branch | Commit or digest | Evidence |
|---|---|---|---|
| OCTW fork | `https://github.com/myseocompany/OCTW`, `codex/document-aricrm-octw-project` | `1a451a79ed09a0919e74470e239480236ce19efd` | `git rev-parse HEAD` |
| OCTW source audited | `https://github.com/myseocompany/OCTW`, `main` | `299c33b368c579db62339ccdccc51e53bca5345c` | Static audit evidence in `STATUS.md` |
| OCTW upstream comparison | `https://github.com/kumanday/OCTW`, `upstream/main` | `299c33b368c579db62339ccdccc51e53bca5345c` | `git fetch upstream && git log upstream/main -1` |
| AriCRM integration audit | `https://github.com/myseocompany/aricrm.git`, `main` | `4b5539c72cf0a7cab93e7df0ac5920237255bdfd` | Clean detached worktree audit at this SHA; original worktree was not used |
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
| `OCTW_KEK=test-kek-not-production OCTW_JWT_SECRET=test-jwt-not-production OCTW_ZAI_API_KEY=test-provider-key docker compose up -d --build` | Failed before health checks because local port `6379` was already allocated. The partial stack was removed with `docker compose down -v`. |
| `docker compose -f docker-compose.yml -f /private/tmp/octw-compose-test.override.yml up -d --build` with the same test environment | Passed start; DB and Redis reached Docker `healthy`; API and edge processes logged `Application startup complete`. The temporary override removed DB/Redis host ports and added API/edge alternate ports for local validation. |
| `docker compose exec -T octw-api curl -fsS http://127.0.0.1:8000/health` | Passed; returned `{"status":"ok"}`. |
| `uv run pytest -q` | Passed; 33 tests passed with 13 warnings. |
| `docker run --rm --entrypoint /app/.venv/bin/python octw-octw-edge -c '...'` edge `TestClient` health check | Passed; returned `200 {"status":"ok","service":"octw-edge"}`. |
| `curl -fsS http://127.0.0.1:18443/health` after the REL-009 route-order fix | Passed; returned `{"status":"ok","service":"octw-edge"}` from the Compose edge service. |
| `docker compose -f docker-compose.yml -f /private/tmp/octw-compose-test.override.yml down -v` | Passed; stopped and removed API, edge, DB, Redis, network, and the test database volume. |
| Rerun at HEAD `a6b6728` after REL-009 fix | Passed with `docker compose -f docker-compose.yml -f /private/tmp/octw-compose-test.override.yml up -d --build`; DB and Redis reached Docker `healthy`; API `/health` returned `{"status":"ok"}`; edge `/health` returned `{"status":"ok","service":"octw-edge"}`; `docker compose -f docker-compose.yml -f /private/tmp/octw-compose-test.override.yml down -v` removed the stack and test volume. |

## Limitations and closure requirements

- OCTW defaults now pin this image, and the minimal Compose start/health/stop cycle
  passes with a local port override. Full tenant OpenClaw runtime provisioning with the
  pinned digest has not yet been exercised.
- AriCRM needs a dedicated `OpenClawInstance` model/client/jobs, a scoped service
  identity, explicit platform-admin authorization, and an OCTW callback receiver before
  integration implementation can begin; see `PLAN.md` Phase 3.
- Project tests now run through `uv run pytest -q` in this environment. The automated
  suite passed locally; CI confirmation remains the GitHub Actions gate.
- Continue recording the exact committed document revision for each future approval or
  re-audit.

This manifest supports `SPEC.md` §14 and does not change the no-go recommendation in
`STATUS.md`.
