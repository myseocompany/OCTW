# AriCRM + OCTW Adaptation — Goal

## Status

Proposed. No production implementation has started.

- Last reviewed: 2026-07-19
- Source baseline: OCTW `299c33b368c579db62339ccdccc51e53bca5345c`
- Detailed requirements: `SPEC.md`
- Delivery sequence: `PLAN.md`
- Open findings: `STATUS.md`
- Architecture decisions: `DECISIONS.md`

## Context

AriCRM needs a safe way to provision and operate isolated OpenClaw instances for selected tenants without placing Docker, OpenClaw runtimes, or their secrets on the AriCRM application server.

OCTW is the starting point because it already models tenants, container lifecycle, encrypted secrets, provider selection, and an edge proxy. Its current `0.1.0` implementation is not production-ready: provisioning is synchronous, machine-to-machine authentication and idempotency are missing, and its edge, networking, authorization, and gateway configuration require hardening.

## Goal

Turn the OCTW fork into a production-capable OpenClaw control plane consumed by AriCRM through a private, versioned API.

- AriCRM remains the system of record for customers, users, plans, entitlements, and billing.
- OCTW owns OpenClaw runtime identity, provisioning operations, encrypted runtime secrets, container state, and infrastructure events.
- OpenClaw remains an upstream dependency; this project will not fork its core.

## Desired outcome

An authorized AriCRM platform administrator can request, inspect, start, stop, and deprovision an OpenClaw instance for a tenant. Operations are asynchronous, idempotent, auditable, and recoverable. A failure in OCTW or one tenant runtime must not interrupt AriCRM or another tenant.

## In scope

- Harden OCTW authentication, authorization, edge, Docker networking, secret handling, and runtime isolation.
- Add a machine-to-machine API contract for AriCRM.
- Add durable operations with idempotency, retries, rollback, locking, and reconciliation.
- Maintain a stable mapping between AriCRM tenants and OCTW instances.
- Support health, resource limits, audit events, metrics, backups, and signed callbacks.
- Seed versioned OpenClaw workspace templates per tenant.
- Deploy OCTW separately from the AriCRM production host.
- Pilot with a small allowlist before general availability.

## Out of scope

- Rewriting OCTW in PHP or letting Laravel control Docker directly.
- Forking OpenClaw.
- Sharing AriCRM and OCTW databases, Redis, filesystems, or credentials.
- Replacing AriCRM's existing conversational `AiAgent` implementation.
- Giving OpenClaw direct database access to AriCRM.
- Allowing unreviewed actions to send messages, delete records, spend money, or change tenant configuration.
- Tenant self-service before quotas, billing, abuse controls, and operational evidence exist.

## Success criteria

These criteria are directional. The measurable pilot thresholds and abort conditions in
`SPEC.md` §13 are normative for acceptance.

1. Repeated equivalent requests never create duplicate instances.
2. Provisioning returns an operation ID immediately and runs outside the HTTP request.
3. AriCRM can recover authoritative state by polling even if callbacks are lost.
4. HTTP and WebSocket access enforce tenant authorization.
5. Internal endpoints require service authentication and private-network access.
6. OpenClaw gateways are reachable only through the authorized edge.
7. Provider access uses controlled egress.
8. Secrets never appear in responses, logs, metrics, callbacks, or plaintext config.
9. Failed operations leave no untracked container, network, volume, secret, or row.
10. End-to-end tests cover lifecycle, isolation, failure recovery, and deletion.
11. Resource exhaustion in one tenant satisfies the 30-minute isolation test and control-plane latency threshold in `SPEC.md` §13 without affecting AriCRM or another tenant.
12. Pilot telemetry attributes availability, resource use, provider cost, and operator actions per tenant.
13. The audited source, OpenClaw digest, validation evidence, decisions, and project documents form the committed reproducible baseline required by `SPEC.md` §14.

## Product principle

Customers experience an AriCRM capability, not an infrastructure product named OCTW. AriCRM presents the workflow and commercial policy; OCTW supplies the isolated runtime.
