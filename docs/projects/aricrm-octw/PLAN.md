# AriCRM + OCTW Adaptation — Implementation Plan

## Status

Planning only. OCTW is hardened before AriCRM depends on it.

- Last reviewed: 2026-07-19
- Source baseline: OCTW `299c33b368c579db62339ccdccc51e53bca5345c`
- Requirements: `SPEC.md`
- Findings and evidence: `STATUS.md`
- Approval record: `DECISIONS.md`

Every task cites the specification section that defines its acceptance requirement.
Closing a checkbox requires code, automated evidence where applicable, and an update to
`STATUS.md`; documentation-only closure is insufficient.

## Phase 0 — Versioned and reproducible baseline

- [x] Fork `kumanday/OCTW` into `myseocompany/OCTW`. (`SPEC.md` §14)
- [x] Keep `origin` on the fork and `upstream` on the original. (`SPEC.md` §14)
- [x] Complete a static architecture and security audit at OCTW SHA `299c33b368c579db62339ccdccc51e53bca5345c`. (`SPEC.md` §14)
- [x] Commit all files under `docs/projects/aricrm-octw`; the document set was introduced by commit `1f7b660`. (`SPEC.md` §14)
- [ ] Create the baseline manifest with OCTW/upstream SHA, AriCRM SHA, OpenClaw version/digest, tool versions, commands, results, limitations, date, and reviewer. (`SPEC.md` §14)
- [ ] Record which findings remain after source commits `6c94917`, `450f302`, and `299c33b`; do not infer closure from commit titles. (`SPEC.md` §14; `STATUS.md`)
- [ ] Approve `GOAL.md` and `SPEC.md`, and resolve Proposed decisions D-010 through D-013. (`SPEC.md` status; `DECISIONS.md`)
- [ ] Obtain privacy/legal and operations approval for D-013 or replace its proposed values. (`SPEC.md` §3 and §10.1)
- [ ] Define CI, branch protection, releases, dependency updates, and the environment matrix. (`SPEC.md` §14)
- [ ] Record and test the supported OpenClaw version and immutable image digest. (`SPEC.md` §3 and §14)

Exit: the documents and evidence are committed, the baseline is reproducible, no
required decision remains Proposed, and every open finding maps to an implementation
task.

## Phase 1 — Functional and security baseline

### Startup safety

- [ ] Add a production-mode startup guard that rejects development JWT credentials, missing/invalid KEK, unpinned OpenClaw images, public PostgreSQL/Redis configuration, and enabled development magic-link behavior. (`SPEC.md` §4)
- [ ] Add positive and negative startup-configuration tests for every rejected condition. (`SPEC.md` §4 and §13)

### Edge and networking

- [ ] Implement the approved D-010 edge trust model and document its network policy. (`SPEC.md` §2.1 and §8)
- [ ] Replace hard-coded loopback control-API discovery with authenticated configuration/service DNS. (`SPEC.md` §2.1 and §8)
- [ ] Let only the worker attach/detach the edge to tenant ingress networks. (`SPEC.md` §2.1)
- [ ] Proxy WebSocket with the same authorization decision as HTTP. (`SPEC.md` §4 and §8)
- [ ] Add controlled provider egress and block metadata, control-plane, host, and cross-tenant destinations. (`SPEC.md` §8)
- [ ] Add streaming body limits, connect/read/write/idle timeouts, safe header allowlists, CSRF/origin protection, rate limits, and activity tracking. (`SPEC.md` §8)

### Access control

- [ ] Remove development magic-link token disclosure and prevent it from starting in production. (`SPEC.md` §4)
- [ ] Replace the misleading internal-router mTLS docstring with implemented service authentication and network policy. (`SPEC.md` §4)
- [ ] Enforce immutable instance authorization before route resolution and wake-up. (`SPEC.md` §2.1, §4, and §8)
- [ ] Restrict provisioning to the AriCRM service scope, platform-admin attestation, OCTW allowlist, entitlement, quota, and capacity. (`SPEC.md` §4)
- [ ] Configure gateway auth, trusted proxies, allowed users, and explicit origins; remove `dangerouslyAllowHostHeaderOriginFallback`. (`SPEC.md` §4)

### Orchestration and persistence

- [ ] Move all Docker work out of async API handlers into a constrained durable worker. (`SPEC.md` §2 and §10)
- [ ] Use machine-readable onboarding with pinned images and fail on every unsupported non-zero exit. (`SPEC.md` §7 and §10)
- [ ] Add retry-safe steps, compensation, resource labels/inventory, locks, reconciliation, and orphan detection. (`SPEC.md` §6, §7, and §10)
- [ ] Start and test the hibernation scheduler with reliable HTTP/WebSocket activity updates, or disable hibernation explicitly. (`SPEC.md` §8 and §10)
- [ ] Make PostgreSQL and Redis private and remove unsafe defaults/listeners. (`SPEC.md` §2 and §4)
- [ ] Separate privileged Docker access from the public API and edge. (`SPEC.md` §2)
- [ ] Create actual Alembic revisions, remove runtime `Base.metadata.create_all`, and test upgrade/downgrade on a representative database. (`SPEC.md` §10)

### Phase 1 tests

- [ ] Add integration tests for database, vault, API, startup guards, service auth, and authorization. (`SPEC.md` §4 and §13)
- [ ] Add Docker lifecycle and pinned-onboarding end-to-end tests. (`SPEC.md` §7, §10, and §13)
- [ ] Add HTTP/WebSocket, cross-tenant, CSRF, SSRF, wrong-scope, and replay denial tests. (`SPEC.md` §8 and §13)
- [ ] Add failure-injection, compensation, hibernation, and orphan-cleanup tests. (`SPEC.md` §6, §10, and §13)

Exit: one isolated instance can be safely provisioned, authorized, accessed, hibernated,
restarted, stopped, and cleaned through tested low-level primitives without AriCRM; the
Phase 1 P0 findings in `STATUS.md` are closed with evidence. Durable platform
deprovisioning and tombstones remain a Phase 2 contract.

## Phase 2 — AriCRM control-plane contract

- [ ] Add external references, desired generations, tombstones, operation/outbox rows, resource inventory, and database constraints through Alembic. (`SPEC.md` §3, §5, §6, and §10.1)
- [ ] Implement D-011 idempotency for every mutation with canonical hashes, 30-day retention, durable uniqueness, replay, and conflicting-key rejection. (`SPEC.md` §5)
- [ ] Implement the durable operation worker, safe cancellation/retry, stale-generation protection, and reconciler. (`SPEC.md` §5 through §7)
- [ ] Implement `/api/v1/platform` instance, operation, profile, and stable error contracts, including ETags and cursor pagination. (`SPEC.md` §5)
- [ ] Implement D-012 secret staging, opaque references, slot allowlists, binding, metadata, rotation, revocation, expiry, and redaction. (`SPEC.md` §9.1)
- [ ] Implement ordered deprovisioning, credential revocation, verified resource removal, tombstones, and retention jobs. (`SPEC.md` §10.1)
- [ ] Add scoped machine authentication, actor context, request IDs, and separate internal identities. (`SPEC.md` §4)
- [ ] Implement signed callback canonicalization, key rotation, replay defense, retries, dead-letter queue, sequencing, and polling recovery. (`SPEC.md` §5 Events)
- [ ] Publish OpenAPI, JSON schemas, contract fixtures, stable error codes, and compatibility policy. (`SPEC.md` §5)
- [ ] Add immutable provider, resource, and workspace-template profiles with required secret slots and image pins. (`SPEC.md` §3 and §9)
- [ ] Add contract tests for duplicates, concurrency, stale ETags/generations, secret redaction, deletion, and event reordering. (`SPEC.md` §5, §9.1, §10.1, and §13)

Exit: a test client drives every lifecycle and secret operation only through the platform
API, and every retry/concurrency/deletion invariant has automated evidence.

## Phase 3 — AriCRM integration

- [ ] Add a dedicated `OpenClawInstance` model with the fields in `SPEC.md` §12; do not reuse `AiAgent`.
- [ ] Add an OCTW client with strict timeouts, retry classification, idempotency keys, ETags, and correlation IDs. (`SPEC.md` §5)
- [ ] Add queued provision/lifecycle/poll/reconciliation jobs that preserve desired generation. (`SPEC.md` §5 and §6)
- [ ] Add write-only secret submission/reference storage without persisting values. (`SPEC.md` §9.1 and §12)
- [ ] Add an idempotent signed-callback receiver with replay window, sequence-gap polling, and platform audit events. (`SPEC.md` §5 Events)
- [ ] Add platform-admin attestation, entitlement, allowlist, quota, budget, and kill-switch checks. (`SPEC.md` §4 and §13)
- [ ] Add superadmin state, health, provision, retry, start, stop, restart, disable, secret rotation, and deprovision controls. (`SPEC.md` §5, §9.1, and §10.1)
- [ ] Test duplicates, lost responses, delayed/reordered callbacks, outages, stale state, permissions, and secret non-retention. (`SPEC.md` §13)

Exit: an AriCRM platform administrator manages an allowlisted test tenant without direct
OCTW access, and polling repairs every simulated callback gap.

## Phase 4 — Staging and pilot

- [ ] Provision a dedicated OCTW host on AriCRM's private network. (`SPEC.md` §2)
- [ ] Begin with 4 vCPU/8 GB RAM only as a measured pilot hypothesis; record load assumptions and resize/admission thresholds. (`SPEC.md` §13)
- [ ] Configure TLS, firewall, identities, backups, monitoring, alerts, retention jobs, and emergency disablement. (`SPEC.md` §2, §10.1, and §11)
- [ ] Demonstrate control-plane and tenant-workspace RPO/RTO in an isolated restore exercise. (`SPEC.md` §10.1 and §13)
- [ ] Instrument every §13 gate: API latency, convergence, drift, cross-tenant denials, resource isolation, operations count, resource inventory, and provider spend. (`SPEC.md` §11 and §13)
- [ ] Run one internal instance, then up to three explicit pilot tenants with narrow tools, human approval, budgets, and kill switches. (`SPEC.md` §13)
- [ ] Run at least 14 consecutive days and 100 lifecycle operations, including the required failure, concurrency, callback, restore, deletion, and 30-minute exhaustion scenarios. (`SPEC.md` §13)
- [ ] Abort and reset the observation window on any §13 critical condition. (`SPEC.md` §13)

Exit: every measurable gate in `SPEC.md` §13 passes, D-013 is approved, no P0/P1 remains,
and no untracked runtime resource exists.

## Phase 5 — Production readiness

- [ ] Close pilot findings and repeat security, isolation, deletion, and restore tests. (`SPEC.md` §13)
- [ ] Define support, incident, privacy, security, and data-deletion ownership. (`SPEC.md` §10.1 and §13)
- [ ] Add canary image/template rollout and rollback. (`SPEC.md` §3 and §9)
- [ ] Add capacity forecasting and admission control from measured pilot data. (`SPEC.md` §4 and §13)
- [ ] Add billing/entitlement enforcement before self-service. (`SPEC.md` §4; `GOAL.md` Out of scope)
- [ ] Reapprove retention, privacy, deletion, and disaster-recovery policy for general availability. (`DECISIONS.md` D-013; `SPEC.md` §10.1)
- [ ] Revisit D-010 and explicitly accept the shared-edge blast radius or implement stronger per-tenant ingress. (`SPEC.md` §2.1)

## Critical path

```text
committed reproducible baseline and approved decisions
  -> startup, auth, edge, networking, migrations, and worker safety
  -> durable idempotent operations, secret references, and verified deletion
  -> versioned AriCRM contract and integration
  -> instrumented restore, isolation, and failure tests
  -> 14-day measurable pilot gate
  -> production approval
```
