# AriCRM + OCTW Adaptation — Technical Specification

## Status

Approved for implementation planning. Production approval still requires the
reproducible baseline evidence in section 14, closed P0 findings, and passing
acceptance tests.

- Last reviewed: 2026-07-19
- Source baseline: OCTW `299c33b368c579db62339ccdccc51e53bca5345c`
- Related documents: `GOAL.md`, `DECISIONS.md`, `PLAN.md`, and `STATUS.md`

## 1. Boundaries

### AriCRM owns

- Tenants, users, roles, plans, entitlements, billing, and operator UI.
- Approval policy for actions initiated through AriCRM.
- The AriCRM-side reference and user-visible status.

### OCTW owns

- OpenClaw instance identity and observed runtime state.
- Provisioning and lifecycle operations.
- Containers, networks, volumes, image pins, workspace templates, and health checks.
- Encrypted runtime secrets, infrastructure audit events, logs, metrics, and backups.

The systems communicate only through versioned APIs and signed events. They never share databases or filesystem paths.

## 2. Deployment

```text
AriCRM -- private network --> OCTW control API --> durable worker --> Docker
                                |                       |
                                +--> PostgreSQL         +--> tenant runtimes
                                +--> Redis/queue

Authorized user --> OCTW edge --> isolated tenant ingress --> OpenClaw gateway
```

- OCTW runs on a host separate from AriCRM.
- The control API is private; PostgreSQL, Redis, Docker, internal endpoints, and gateway ports are not public.
- TLS terminates before the API and edge.
- Privileged Docker access belongs to a constrained worker or socket proxy, not the public API process.
- The API, worker, reconciler, edge, and callback dispatcher are separately deployable processes with separate identities and least-privilege network policy.
- The public API process cannot access the Docker socket. The edge cannot access the Docker socket, PostgreSQL, Redis, the vault, or provider credentials.

### 2.1 Trust boundary and edge decision

Decision reference: `DECISIONS.md` D-010 (Accepted for pilot).

For the pilot, OCTW uses a shared edge as a trusted platform component. It may join each
tenant's ingress network, but only the worker may attach or detach it. A compromised
tenant runtime is in scope and must remain contained; a compromised edge, worker,
Docker daemon, host, or OCTW signing key is a platform-wide incident and is not claimed
to be tenant-contained.

The shared edge therefore:

- runs non-root with a read-only root filesystem, all capabilities dropped, `no-new-privileges`, a restrictive seccomp/AppArmor profile, and no shell or package manager in its runtime image;
- receives routes from an authenticated control-plane interface and never accepts an upstream address from a public request;
- resolves the authenticated user to an immutable `instance_id`, authorizes that instance, and only then resolves the current route or requests wake-up;
- uses a narrowly scoped internal identity that can read sanitized route/health data and request wake-up, but cannot provision, delete, read secrets, or call arbitrary lifecycle endpoints;
- can connect only to the control-plane route service and approved tenant gateway ports; host firewall policy blocks tenant-initiated access to the edge and cross-tenant forwarding;
- is treated as a critical shared dependency with independent patching, audit logging, rate limits, availability monitoring, emergency disablement, and credential rotation.

Before general availability, the pilot threat-model review must either accept this
shared blast radius explicitly or replace it with a stronger per-tenant ingress design.

## 3. Identity

| Field | Purpose |
|---|---|
| `external_system` | Always `aricrm` for this integration |
| `external_ref` | Stable AriCRM tenant UUID |
| `instance_id` | OCTW instance UUID |
| `operation_id` | Durable asynchronous operation UUID |
| `slug` | Human-readable route, never cross-system identity |
| `workspace_template_version` | Reproducible agent behavior |
| `openclaw_image_digest` | Reproducible runtime |

`(external_system, external_ref)` is unique for active instances. The first release permits one active OCTW instance per AriCRM tenant without preventing future one-to-many support.

IDs are immutable and never recycled. A deleted instance remains addressable as a
sanitized tombstone for the retention period. Reuse of an external reference is allowed
only after deletion has succeeded, the seven-day pilot cooldown has elapsed, and a new
idempotent creation request explicitly requests a new instance.

The seven-day value is approved pilot policy under `DECISIONS.md` D-013, not general
availability policy.

## 4. Authentication and authorization

- AriCRM uses a dedicated service identity, never a human magic-link JWT.
- Initial implementation may use a rotatable high-entropy service credential plus TLS, source allowlisting, explicit scopes, and constant-time verification.
- Target implementation uses short-lived client-credential tokens or mTLS.
- Scopes: `instances:read`, `instances:provision`, `instances:operate`, `instances:delete`, `secrets:read_metadata`, and `secrets:write`. Retry and cancellation require the scope of the original operation.
- Platform endpoints reject human session or magic-link JWTs. A valid human JWT is never sufficient to provision or operate infrastructure.
- Provisioning additionally requires an AriCRM platform-admin authorization decision, an OCTW tenant allowlist entry, entitlement, quota, and admission-control capacity. Authentication without these checks returns `403` and creates no operation or infrastructure.
- AriCRM sends immutable actor and tenant IDs as service-authenticated audit context. OCTW treats the AriCRM service identity as the attester, never trusts equivalent headers from public edge traffic, and still enforces its own scopes, allowlist, profiles, quota, and capacity.
- Every request records service identity, request ID, action, target, source, and result.
- Edge access requires both authentication and authorization for the requested instance.
- The edge overwrites identity and forwarding headers and applies identical policy to HTTP and WebSocket traffic.
- OpenClaw gateway auth, trusted proxies, allowed users, and allowed origins are explicit. Dangerous Host-header fallback is disabled.
- Internal endpoints require a separate internal identity; network placement alone is insufficient.
- Production refuses to start with development credentials, a missing KEK, public database/cache listeners, or development magic-link behavior enabled.

## 5. Platform API

Decision reference: `DECISIONS.md` D-011 (Accepted).

New endpoints live under `/api/v1/platform`. JSON uses `snake_case`. Every mutating
request requires `X-Request-Id` and `Idempotency-Key`, including start, stop, restart,
secret mutation, retry, and deletion.

Idempotency is scoped by service identity, HTTP route, semantic action, and key. OCTW
stores the canonical JSON request hash, original status, response body, resource IDs,
and operation ID for at least 30 days. Retrying the same key and equivalent payload
returns the original response without repeating side effects. Reusing the key with a
different payload returns `409 IDEMPOTENCY_KEY_REUSED`. Concurrent first submissions
are serialized by a database uniqueness constraint; correctness cannot depend only on
Redis.

### Provision

`POST /api/v1/platform/instances` returns `202 Accepted`.

```json
{
  "external_system": "aricrm",
  "external_ref": "ari-tenant-uuid",
  "slug": "tenant-slug",
  "name": "Tenant name",
  "provider_profile": "platform-default@1",
  "resource_profile": "pilot-standard@1",
  "workspace_template": "aricrm-operator",
  "workspace_template_version": "1.0.0",
  "secret_refs": {
    "provider.primary_api_key": "octw-secret://opaque-uuid#v1"
  }
}
```

```json
{
  "operation_id": "uuid",
  "instance_id": "uuid",
  "status": "accepted"
}
```

The same key and equivalent payload return the original result. Reusing a key with a different payload returns `409`.

### Read and operate

- `GET /api/v1/platform/instances/{instance_id}`
- `GET /api/v1/platform/instances/by-external-ref/{external_ref}`
- `POST /api/v1/platform/instances/{instance_id}/start`
- `POST /api/v1/platform/instances/{instance_id}/stop`
- `POST /api/v1/platform/instances/{instance_id}/restart`
- `DELETE /api/v1/platform/instances/{instance_id}`
- `GET /api/v1/platform/operations/{operation_id}`
- `POST /api/v1/platform/operations/{operation_id}/retry`
- `POST /api/v1/platform/operations/{operation_id}/cancel`

Lifecycle writes return `202` and an operation. Responses expose sanitized state and errors, never secret values or raw Docker internals.

Start and stop express desired state and may complete as a successful no-op. Restart is
an explicit action and is deduplicated only by its idempotency key. Delete is terminal
once accepted: later non-read operations return `409 INSTANCE_DELETING` or
`410 INSTANCE_DELETED`.

Retry creates a new operation linked through `retry_of_operation_id`; it never mutates
the historical terminal result. Cancellation is accepted only while an operation is
`accepted` or `queued`. A running operation returns `409 OPERATION_NOT_CANCELLABLE`
unless its current step declares and executes a safe cancellation checkpoint.

Each instance has a monotonically increasing `desired_generation`. Each operation
captures the generation it intends to apply. A worker holding the per-instance lock
must re-read that generation before every external side effect and before committing
observed state. A stale operation cannot overwrite a newer desired state. Delete
supersedes queued non-delete operations; running operations reach a safe checkpoint and
then compensate or stop.

### Response contracts

An instance response contains at least:

```json
{
  "instance_id": "uuid",
  "external_system": "aricrm",
  "external_ref": "ari-tenant-uuid",
  "slug": "tenant-slug",
  "desired_state": "running",
  "desired_generation": 3,
  "observed_state": "running",
  "health": "healthy",
  "provider_profile": "platform-default@1",
  "resource_profile": "pilot-standard@1",
  "workspace_template": "aricrm-operator@1.0.0",
  "openclaw_image_digest": "sha256:...",
  "latest_operation_id": "uuid",
  "created_at": "RFC3339 timestamp",
  "updated_at": "RFC3339 timestamp",
  "deleted_at": null
}
```

An operation response contains `operation_id`, `instance_id`, `type`, `status`,
`desired_generation`, `attempt`, `created_at`, `started_at`, `finished_at`, sanitized
`error`, and retryability. Reads return `ETag`; mutating requests that change an
existing instance accept `If-Match` and return `412 PRECONDITION_FAILED` for a stale
version. Collection endpoints use opaque cursor pagination and stable ordering.

Errors use one envelope and stable machine code:

```json
{
  "error": {
    "code": "INSTANCE_DELETING",
    "message": "Sanitized human-readable message",
    "request_id": "uuid",
    "retryable": false,
    "details": {}
  }
}
```

### Events

- `octw.operation.succeeded`
- `octw.operation.failed`
- `octw.instance.state_changed`
- `octw.instance.health_changed`

Callback destinations are deployment configuration, never request-supplied URLs. Each
event has an immutable `event_id`, `event_type`, `occurred_at`, `instance_id`,
`operation_id` when applicable, `sequence`, schema version, and sanitized payload.

Headers are `X-OCTW-Event-Id`, `X-OCTW-Timestamp`, `X-OCTW-Key-Id`, and
`X-OCTW-Signature`. The signature is `v1=<hex HMAC-SHA256>` over
`<unix_timestamp>.<raw_request_body>`. AriCRM verifies the raw body in constant time,
rejects timestamps outside a five-minute replay window, and deduplicates `event_id` for
at least 30 days. Key rotation supports overlapping active key IDs.

Any `2xx` acknowledges delivery. Other responses retry with exponential backoff and
jitter for up to ten attempts and 24 hours, then enter a dead-letter queue and alert.
Delivery order is not guaranteed; consumers use per-instance `sequence` and polling to
recover gaps. Polling remains the correctness path.

## 6. State

```text
operation: accepted -> queued -> running -> succeeded | failed | cancelled | superseded

desired instance state: running | stopped | deleted

observed instance state:
pending | provisioning | running | degraded | paused | stopped |
error | deleting | deleted | unknown
```

Desired and observed state are stored separately. A reconciler attempts convergence and reports persistent drift.

Operation transitions are append-audited and compare-and-set. A failed or cancelled
operation never implies that compensation succeeded; resource inventory and observed
state remain authoritative. Persistent drift older than five minutes alerts during the
pilot.

## 7. Provisioning workflow

1. Authenticate and authorize AriCRM.
2. Validate entitlement, payload, profiles, template version, and image pin.
3. Resolve the idempotency key and external-reference uniqueness.
4. Create instance and operation transactionally; return `202`.
5. A worker acquires a per-instance distributed lock.
6. Create directories and isolated ingress plus controlled egress.
7. Generate and vault the gateway credential.
8. Run supported, non-interactive, machine-readable OpenClaw onboarding.
9. Apply explicit gateway, proxy, model, and workspace configuration.
10. Start the pinned image with security and resource limits.
11. Connect only the edge to tenant ingress.
12. Verify health, authenticated HTTP, WebSocket, and provider egress.
13. Mark success and emit audit/event records.

Each step must be retry-safe or have a compensating action. Human-readable log fragments are not a success contract.

No failed step deletes the instance or operation row. It records the exact completed
steps and owned resource IDs so reconciliation can retry or compensate without guessing.

## 8. Networking and edge

- Each tenant gets isolated ingress shared only with the edge.
- Outbound traffic goes through an egress proxy or explicit egress network.
- Tenant containers have no host ports, Docker socket, host namespace, metadata service, control network, database, Redis, or cross-tenant access.
- Edge discovers the control API through configuration, joins tenant networks through the orchestrator, proxies HTTP and WebSocket, authorizes before wake-up, and applies timeouts, body/connection/rate limits, safe headers, and activity tracking.
- HTTP and WebSocket use the same immutable instance authorization decision. Cookie-based browser writes require origin validation and CSRF protection; bearer credentials are never placed in URLs.
- The proxy streams bounded request/response bodies, removes hop-by-hop and untrusted identity headers, sets explicit connect/read/write/idle timeouts, and does not reflect upstream security or forwarding headers without an allowlist.

## 9. Templates and secrets

Versioned workspace templates may contain `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `HEARTBEAT.md`, and optionally `BOOTSTRAP.md`.

- Memory, sessions, credentials, and generated tenant data are never committed here.
- Template upgrades require backup, compatibility checks, and rollback.
- AriCRM submits profiles and allowlisted secret references, never arbitrary environment-variable dictionaries.
- Secrets are encrypted, redacted, write-only through APIs, and rotated with an audit event.

### 9.1 Secret reference contract

Decision reference: `DECISIONS.md` D-012 (Accepted).

A secret slot is a stable, allowlisted semantic name declared by a versioned provider
profile or workspace template, for example `provider.primary_api_key`. Slots map to
environment variables or OpenClaw `SecretRef` targets only inside OCTW configuration;
the caller cannot choose an environment-variable name.

`secret_ref` is an opaque OCTW identifier with instance/external-reference ownership,
slot, version, state, and timestamps. Its serialized form is
`octw-secret://<opaque-uuid>#v<version>`. It contains no provider, path, environment
variable, or secret value. OCTW validates that a reference belongs to the same tenant
and allowed slot before binding it.

The write-only contract is:

- `POST /api/v1/platform/secrets` stages a value for `external_system`, `external_ref`, and an allowlisted `slot`; it returns reference metadata and never the value. Unbound staged secrets expire and are destroyed after 24 hours.
- Provision accepts `secret_refs`, a slot-to-reference map. Required slots are derived from the selected immutable profiles and template; missing or incompatible slots return `422 SECRET_SLOT_REQUIRED` before infrastructure is created.
- `GET /api/v1/platform/instances/{instance_id}/secrets` returns metadata only.
- `POST /api/v1/platform/secrets/{secret_ref}/rotate` accepts a new value, creates a version, emits an audit event, and creates the required reload/restart operation. The prior version is retained encrypted for a 24-hour rollback window and then destroyed.
- `DELETE /api/v1/platform/secrets/{secret_ref}` revokes the binding and creates any required stop/reload operation; deletion is rejected while an active profile requires the slot.

Provider profiles may bind platform-scoped secrets held entirely by OCTW. AriCRM may
transmit a new tenant value once over the write-only endpoint but never persists or
retrieves it. Request bodies containing values are excluded from access logs, traces,
metrics, error details, callback payloads, and dead-letter records. Secret resolution
occurs only in the worker immediately before runtime creation; plaintext is never
written to generated configuration or persistent disk.

## 10. Runtime and reliability

- Non-root UID, all capabilities dropped, `no-new-privileges`, explicit writable mounts, resource and log limits, no host ports, and pinned image digest.
- Docker work never blocks the API event loop.
- Durable queue, bounded retry, per-instance locks, failure classification, and periodic reconciliation are mandatory.
- Orphan resources are reported before safe cleanup.
- Production uses versioned migrations, not runtime `create_all`.
- Backups require demonstrated restore tests.

### 10.1 Deprovisioning, retention, and recovery

Decision reference: `DECISIONS.md` D-013 (Accepted for pilot).

`DELETE` first commits desired state `deleted`, a deletion operation, an audit event,
and an outbox event transactionally. The worker then, in order:

1. disables new edge traffic and wake-up;
2. revokes gateway and callback credentials;
3. stops and removes runtime/init containers;
4. detaches and removes tenant ingress/egress networks;
5. destroys live secret material, workspace, state, and volumes according to policy;
6. verifies by labels and inventory that no owned runtime resource remains;
7. writes the sanitized tombstone and terminal event.

Failure leaves the instance tracked as `deleting` or `error`, including owned resource
IDs; it never removes the database row prematurely. Reconciliation retries safe steps
and alerts instead of blindly deleting unlabeled resources.

Pilot retention defaults are: idempotency records and callback deduplication 30 days;
operations and sanitized operational logs 90 days; audit/tombstone metadata 365 days;
live secret ciphertext destroyed at verified deletion; encrypted backup copies expire
within 30 days. Audit data never retains secret values or tenant-generated content.
These defaults are approved for the pilot and require reapproval before general
availability.

Pilot recovery objectives are control-plane metadata RPO 15 minutes/RTO 4 hours and
tenant workspace RPO 24 hours/RTO 8 hours. A quarterly restore exercise must recreate
metadata and one representative tenant in an isolated environment without exposing
production credentials.

## 11. Observability

Track operation step duration/errors; instance state, health and resource use; HTTP/WebSocket authorization and latency; queue depth; lock contention; callbacks; reconciliation drift; backup age; and provider usage/cost where available. Correlation IDs connect AriCRM, OCTW, worker, edge, and callbacks.

Metrics and logs use immutable instance/tenant IDs, not secret values or unbounded
customer-controlled labels. Audit events record actor, service identity, authorization
decision, request ID, target, old/new desired generation, result, and source; they are
append-only to application identities.

## 12. AriCRM record

AriCRM creates a dedicated OpenClaw-instance model instead of reusing `AiAgent`. It stores `tenant_id`, `octw_instance_id`, `latest_operation_id`, slug, desired/observed state, health, template/runtime versions, sanitized last error, and synchronization timestamps. It stores no OCTW secret values.

## 13. Acceptance gates

- Critical findings in `STATUS.md` are closed.
- Docker end-to-end, HTTP/WebSocket isolation, failure-injection, retry, cleanup, and restore tests pass.
- OpenClaw security audit findings are reviewed for the deployed configuration.
- One tenant's resource exhaustion does not affect the control plane or another tenant.
- AriCRM recovers state by polling after missed callbacks.
- Operator runbooks cover provision, retry, restart, disable, restore, rotate, and deprovision.

The pilot gate is measurable:

- run for at least 14 consecutive days with one internal and up to three allowlisted pilot tenants;
- execute at least 100 lifecycle operations, including duplicate submissions, concurrent conflicting requests, injected worker failure, lost/reordered callbacks, restore, and deletion;
- return `202` from accepted lifecycle writes within two seconds at p95, excluding client network latency;
- converge ordinary desired-state changes within five minutes at p95 and alert on drift older than five minutes;
- pass 100% of HTTP/WebSocket cross-tenant, unauthenticated, wrong-scope, stale-precondition, replay, SSRF, and CSRF denial cases;
- sustain a 30-minute tenant exhaustion test at its configured CPU, memory, PID, connection, and log limits with no control-plane OOM/restart, no state change in another tenant, and control API p95 latency below twice its pre-test baseline;
- demonstrate the stated RPO/RTO in a restore exercise;
- have zero unresolved P0/P1 security or isolation findings and zero untracked runtime resources.

Any critical isolation, unauthorized action, secret exposure, uncontrolled provider spend,
or AriCRM availability incident aborts the pilot and resets the observation window after
remediation.

## 14. Reproducible baseline and approval evidence

Before production approval, a committed baseline manifest must record:

- OCTW fork URL, branch, and full commit SHA;
- upstream OCTW URL and full comparison SHA;
- AriCRM repository and full commit SHA reviewed for the integration;
- supported OpenClaw version, immutable image digest, and interface/configuration version;
- document commit SHA, audit date, reviewer, environment, Python/Docker/tool versions, and exact validation commands/results;
- evidence links or file/line references for every `STATUS.md` finding;
- tests not run, environmental limitations, and the owner/date for closing each limitation.

The OCTW source baseline inspected for this specification is
`299c33b368c579db62339ccdccc51e53bca5345c`. This does not complete the baseline:
the exact approved document revision and executable lifecycle evidence remain required.
The project document set was introduced in commit `1f7b660`;
each approval or re-audit must record the exact repository revision it reviewed.
