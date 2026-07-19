# AriCRM + OCTW Adaptation — Status

## Snapshot

- Date: 2026-07-19
- Stage: audit and planning
- Implementation: not started
- Production readiness: no-go
- OCTW fork: `https://github.com/myseocompany/OCTW`
- OCTW upstream: `https://github.com/kumanday/OCTW`
- Branch: `main`
- OCTW source audited: `299c33b368c579db62339ccdccc51e53bca5345c`
- Document revision audited: `a25781e` (docs only; source baseline unchanged)
- Upstream comparison SHA: pending — must be confirmed with `git fetch upstream && git log upstream/main -1` and recorded in the baseline manifest
- AriCRM SHA audited: not recorded — baseline blocker
- OpenClaw version/image digest: not recorded — baseline blocker
- Project-document baseline: introduced in commit `1f7b660`; each approval/re-audit must record its exact reviewed revision
- Requirements: `SPEC.md`
- Delivery tasks: `PLAN.md`
- Architecture decisions: `DECISIONS.md`

The audit evidence below was rechecked against HEAD `299c33b`. That HEAD includes
`6c94917`, `450f302`, and `299c33b`; commit titles are not closure evidence. In
particular, `450f302` did not remove the dangerous Host-header fallback, and `6c94917`
did not implement ordered deletion or tombstones.

## Completed validation

- Confirmed the OCTW fork and upstream remotes at the SHA above.
- Confirmed AriCRM production was reported on `waterfall` without Docker and with approximately 2 vCPU/4 GB RAM; this infrastructure evidence still needs a reproducible AriCRM/host baseline artifact.
- Chose a separate OCTW host; see `DECISIONS.md` D-002.
- Parsed/compiled the current Python source and tests successfully with `python3 -m compileall -q src tests` using Python 3.14.5.
- Validated `docker compose config -q`; it passed while warning that `OCTW_KEK` was unset and defaulted to an empty string.
- Reconciled and versioned `GOAL.md`, `SPEC.md`, `PLAN.md`, `STATUS.md`, and `DECISIONS.md`; the set was introduced in commit `1f7b660`.

These checks do not establish runtime correctness or production readiness.

## Validation limitations

- `uv` and `pytest` are unavailable, so the automated suite was not executed.
- No end-to-end Docker/OpenClaw, HTTP/WebSocket, failure-injection, load, backup, restore, or deletion test was performed.
- No AriCRM source SHA or OpenClaw image digest is attached to this audit.
- The initial document set is tracked; the future approval record must still identify the exact reviewed revision.

## Open findings

Each finding has a stable ID, evidence, specification requirement, and implementation
task. A finding closes only when `PLAN.md` evidence exists at a committed source SHA.

### Resolved — Governance

#### GOV-001 — Project documents were outside version control

Resolved by commit `1f7b660`, which introduced all five files under
`docs/projects/aricrm-octw`. Approval remains blocked by GOV-002 and Proposed decisions,
not by absence of tracked documents.

- Requirement: `SPEC.md` §14.
- Evidence: commit `1f7b660`; `PLAN.md` Phase 0.

### P0 — Governance and baseline

#### GOV-002 — Baseline lacks AriCRM and OpenClaw identity

The audit records OCTW HEAD but not the AriCRM commit, supported OpenClaw version/image
digest, document SHA, reviewer artifact, or exact environment manifest.

- Requirement: `SPEC.md` §14.
- Task: `PLAN.md` Phase 0 — baseline manifest and pinned OpenClaw digest.

### P0 — Functional

#### FUN-001 — Edge resolves the control API through loopback

The edge hard-codes `http://127.0.0.1:8000` although edge and API are separate Compose
services (`src/octw/edge/proxy.py:23`; `docker-compose.yml:61-76`).

- Requirement: `SPEC.md` §2.1 and §8.
- Task: `PLAN.md` Phase 1 — authenticated configuration/service DNS.

#### FUN-002 — Edge is not attached to tenant ingress networks

`connect_edge_to_network` exists but has no caller; Compose attaches the edge only to
`octw_control` (`src/octw/orchestrator/docker_orch.py:117-123`;
`docker-compose.yml:75-76`).

- Requirement: `SPEC.md` §2.1 and §8; proposed decision D-010.
- Task: `PLAN.md` Phase 1 — worker-managed network attachment.

#### FUN-003 — WebSocket is not proxied

The edge defines only HTTP `api_route` methods and no WebSocket route
(`src/octw/edge/proxy.py:90-129`).

- Requirement: `SPEC.md` §4, §8, and §13.
- Task: `PLAN.md` Phase 1 — policy-identical HTTP/WebSocket proxying and denial tests.

#### FUN-004 — Tenant networks have no controlled provider egress

Tenant networks are created with `internal=True` and no egress path is attached
(`src/octw/orchestrator/docker_orch.py:92-106`).

- Requirement: `SPEC.md` §8.
- Task: `PLAN.md` Phase 1 — controlled egress and blocked-destination tests.

#### FUN-005 — Gateway and edge authentication are not aligned

Provisioning enables trusted-proxy mode, but generated gateway configuration does not
establish the complete trusted-proxy/allowed-user contract and enables unsafe origin
fallback (`src/octw/api/routers/provision_router.py:101-107`;
`src/octw/orchestrator/docker_orch.py:235-242`).

- Requirement: `SPEC.md` §4 and §8.
- Task: `PLAN.md` Phase 1 — explicit gateway auth, proxies, users, and origins.

#### FUN-006 — Edge authentication does not authorize the requested tenant

The edge checks that a JWT exists and immediately resolves the caller-controlled slug;
it never checks membership or binds authorization to `instance_id`
(`src/octw/edge/proxy.py:94-103`).

- Requirement: `SPEC.md` §2.1, §4, and §8.
- Task: `PLAN.md` Phase 1 — immutable instance authorization before route/wake-up.

### P0 — Security

#### SEC-001 — Internal lifecycle endpoints are unauthenticated

The module claims “mTLS only in production,” but its endpoints have no authentication
dependency (`src/octw/api/routers/internal_router.py:1,33-79`). The docstring describes
a control that does not exist.

- Requirement: `SPEC.md` §4.
- Task: `PLAN.md` Phase 1 — implemented internal service identity and network policy.

#### SEC-002 — Development login is an authentication bypass

Login returns a verification token for any supplied email, and verification issues a
JWT (`src/octw/api/routers/auth_router.py:33-56`).

- Requirement: `SPEC.md` §4.
- Task: `PLAN.md` Phase 1 — remove disclosure and add production startup rejection.

#### SEC-003 — Dangerous Host-header origin fallback remains enabled

`dangerouslyAllowHostHeaderOriginFallback` is hard-coded to `True`
(`src/octw/orchestrator/docker_orch.py:235-242`). Commit `450f302` did not close this
finding.

- Requirement: `SPEC.md` §4.
- Task: `PLAN.md` Phase 1 — explicit origins and fallback removal.

#### SEC-004 — Public API runs as root with the Docker socket

Compose runs `octw-api` as `0:0` and mounts `/var/run/docker.sock`
(`docker-compose.yml:32-52`).

- Requirement: `SPEC.md` §2 and §10.
- Task: `PLAN.md` Phase 1 — constrained worker/socket proxy separated from API and edge.

#### SEC-005 — PostgreSQL and Redis use unsafe development exposure/defaults

PostgreSQL uses password `octw`; both services publish host ports
(`docker-compose.yml:2-9,20-23`).

- Requirement: `SPEC.md` §2 and §4.
- Task: `PLAN.md` Phase 1 — private services, safe credentials, and startup guard.

#### SEC-006 — Secret input is arbitrary and contradicts D-012

Provisioning accepts `dict[str, str]` and maps each caller-controlled name directly to
an environment variable; the secret API also accepts a caller-selected target variable
(`src/octw/api/routers/provision_router.py:26-33,119-125`;
`src/octw/api/routers/secrets_router.py:33-48`).

- Requirement: `SPEC.md` §9.1; proposed decision D-012.
- Task: `PLAN.md` Phase 2 — allowlisted slots and opaque staged references.

#### SEC-007 — Any authenticated user can provision infrastructure

Provisioning requires only `get_current_user`; it has no platform scope, admin
attestation, allowlist, entitlement, quota, or capacity check
(`src/octw/api/routers/provision_router.py:59-67`). Combined with SEC-002, this permits
unauthorized infrastructure/provider consumption.

- Requirement: `SPEC.md` §4.
- Task: `PLAN.md` Phase 1 — scoped service-only provisioning and admission controls.

#### SEC-008 — No production startup guard exists

Settings retain development DB/Redis/JWT/image defaults, and application lifespan only
runs schema creation (`src/octw/common/config.py:9-24`;
`src/octw/api/app.py:20-24`). Missing KEK and public listeners are not rejected.

- Requirement: `SPEC.md` §4.
- Task: `PLAN.md` Phase 1 — startup guard and negative tests.

### P0 — Reliability and data lifecycle

#### REL-001 — Blocking Docker work runs in async request handlers

Provisioning executes init/configuration/container operations before responding
(`src/octw/api/routers/provision_router.py:128-150`); runtime endpoints call synchronous
orchestration through `TenantService` (`src/octw/api/routers/runtime_router.py:31-80`).

- Requirement: `SPEC.md` §2, §5, and §10.
- Task: `PLAN.md` Phase 1/2 — durable worker and `202` operations.

#### REL-002 — No durable operations, idempotency, or distributed locks

Mutation routes return immediate results and expose no idempotency-key dependency or
operation record (`src/octw/api/routers/provision_router.py:59-67`;
`src/octw/api/routers/runtime_router.py:31-80`;
`src/octw/api/routers/tenants_router.py:33-42,99-109`).

- Requirement: `SPEC.md` §5 and §6; proposed decision D-011.
- Task: `PLAN.md` Phase 2 — durable operations, DB uniqueness, canonical hashes, locks, and reconciliation.

#### REL-003 — Failed provisioning can leave untracked resources

Tenant directories and a network are created before the database transaction commits,
without compensation (`src/octw/orchestrator/tenant_service.py:52-96`).

- Requirement: `SPEC.md` §7 and §10.
- Task: `PLAN.md` Phase 1 — inventory, retry-safe steps, compensation, and orphan tests.

#### REL-004 — Onboarding treats log text as success

A non-zero exit is accepted when output contains `Updated` and `openclaw.json`
(`src/octw/orchestrator/docker_orch.py:184-210`).

- Requirement: `SPEC.md` §7.
- Task: `PLAN.md` Phase 1 — supported machine-readable success contract.

#### REL-005 — Hibernation is defined but not running

`HibernationScheduler` exists (`src/octw/orchestrator/hibernation.py:18-74`) but has no
instantiation site or caller, and edge requests do not update activity
(`src/octw/edge/proxy.py:90-129`).

- Requirement: `SPEC.md` §8 and §10.
- Task: `PLAN.md` Phase 1 — start/test it or disable it explicitly.

#### REL-006 — Schema lifecycle has no application revisions

The migrations directory contains only `env.py`, while application startup calls
`Base.metadata.create_all` (`src/octw/api/app.py:20-24`).

- Requirement: `SPEC.md` §10.
- Task: `PLAN.md` Phase 1 — real Alembic revisions and upgrade/downgrade tests.

#### REL-007 — Deletion has no ordered teardown or tombstone

Deletion performs three synchronous cleanup calls and then hard-deletes the database row
(`src/octw/orchestrator/docker_orch.py:452-456`;
`src/octw/orchestrator/tenant_service.py:127-147`). It does not disable ingress, revoke
credentials, verify inventory, retain a tombstone, or recover partial failure.

- Requirement: `SPEC.md` §10.1; proposed decision D-013.
- Task: `PLAN.md` Phase 2 — ordered durable deprovisioning and retention jobs.

#### REL-008 — Backup, restore, retention, RPO, and RTO are unvalidated

No completed runtime validation demonstrates the objectives proposed in `SPEC.md` §10.1.

- Requirement: `SPEC.md` §10.1 and §13; proposed decision D-013.
- Task: `PLAN.md` Phase 4 — backup configuration and isolated restore exercise.

### P1 — AriCRM integration and production policy

#### INT-001 — AriCRM service identity and scopes do not exist

Only human JWT authentication exists (`src/octw/api/auth.py:17-54`).

- Requirement/task: `SPEC.md` §4; `PLAN.md` Phase 2.

#### INT-002 — External references, generations, operations, and tombstones do not exist

Current tenant tables/models expose none of the platform identity/state contract.

- Requirement/task: `SPEC.md` §3, §5, §6, and §10.1; `PLAN.md` Phase 2.

#### INT-003 — Signed callback/polling contract is not implemented

There is no event outbox, dispatcher, signature, sequence, dead-letter queue, or platform
operation polling endpoint.

- Requirement/task: `SPEC.md` §5 Events; `PLAN.md` Phase 2/3.

#### INT-004 — Versioned profiles and workspace templates do not exist

Current settings use mutable global image/provider configuration
(`src/octw/common/config.py:12-14,34-50`).

- Requirement/task: `SPEC.md` §3 and §9; `PLAN.md` Phase 2.

#### INT-005 — Pilot governance controls and measurable telemetry do not exist

There is no implemented allowlist, quota, admission control, per-tenant cost attribution,
kill switch, §13 gate instrumentation, or approved D-013 retention/recovery policy.

- Requirement/task: `SPEC.md` §4, §11, and §13; `PLAN.md` Phase 3/4.

## Recommendation

Do not approve or deploy OCTW as an AriCRM dependency. Complete the baseline manifest,
resolve D-010 through D-013, and then execute `PLAN.md` Phase 1. Source changes must
close findings by stable ID with automated or reproducible evidence.

## Next action

1. Complete the missing AriCRM/OpenClaw baseline fields and record the exact document revision reviewed.
2. Review and resolve D-010 through D-013.
3. Implement Phase 1 beginning with startup rejection, internal/service authentication,
   edge authorization, Host-header fallback removal, worker separation, and migrations.
