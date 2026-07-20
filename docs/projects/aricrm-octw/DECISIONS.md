# AriCRM + OCTW Adaptation — Decision Log

New decisions receive the next ID and state their status, rationale, and consequences. Superseded decisions remain recorded.

This log is normative for `SPEC.md`. A decision marked Proposed is an approval blocker;
the specification may describe it for review, but implementation must not treat it as
approved policy.

## D-001 — Fork OCTW, not OpenClaw

- Status: Accepted
- Date: 2026-07-19
- Decision: maintain `myseocompany/OCTW`; consume pinned upstream OpenClaw images/interfaces.
- Rationale: required changes belong to the multi-tenant control plane, not OpenClaw core.
- Consequence: keep `kumanday/OCTW` as `upstream` and test every supported OpenClaw upgrade.

## D-002 — Separate OCTW host

- Status: Accepted
- Date: 2026-07-19
- Decision: do not install OCTW or Docker on AriCRM production host `waterfall`.
- Rationale: privileged Docker orchestration and tenant runtimes have different resource and failure characteristics.
- Consequence: independent deployment, monitoring, backup, patching, and a private AriCRM connection.

## D-003 — API integration, never a shared database

- Status: Accepted
- Date: 2026-07-19
- Decision: use a private versioned API and signed events; share no DB, Redis, filesystem, or reusable AriCRM/OCTW/runtime credentials. Dedicated integration authentication and callback-verification material is allowed and independently rotatable.
- Rationale: explicit boundaries limit privilege and allow independent evolution.
- Consequence: polling is the correctness path; callbacks reduce latency; contract tests are mandatory.

## D-004 — Separate from AriCRM `AiAgent`

- Status: Accepted
- Date: 2026-07-19
- Decision: AriCRM models OpenClaw instances separately from conversational `AiAgent` records.
- Rationale: an OCTW instance is infrastructure with workspace, secrets, lifecycle, and potentially several agents.
- Consequence: provisioning an instance does not automatically enable it in conversations.

## D-005 — Asynchronous and idempotent operations

- Status: Accepted
- Date: 2026-07-19
- Decision: lifecycle writes create durable operations and return `202`; creation requires an idempotency key.
- Rationale: Docker pulls, onboarding, verification, and cleanup are slow and partially fallible.
- Consequence: OCTW needs workers, operation storage, locks, and reconciliation; AriCRM handles pending state and polling.
- Follow-up: D-011 extends mandatory idempotency keys from creation to every mutation.

## D-006 — AriCRM tenant UUID as external reference

- Status: Accepted
- Date: 2026-07-19
- Decision: store the AriCRM tenant UUID as `external_ref` under `external_system = aricrm`.
- Rationale: UUIDs are stable; slugs can change or collide.
- Consequence: the pair is unique for active instances and supports direct lookup.

## D-007 — Runtime secrets stay in OCTW

- Status: Accepted
- Date: 2026-07-19
- Decision: OCTW stores and rotates OpenClaw runtime/provider secrets; AriCRM stores references and policy only.
- Rationale: duplicating decryptable values across systems expands exposure.
- Consequence: AriCRM never retrieves values; submission is allowlisted and write-only.

## D-008 — Version templates and pin images

- Status: Accepted
- Date: 2026-07-19
- Decision: every instance records an immutable OpenClaw digest and workspace-template version; production never follows `latest`.
- Rationale: reproducibility, incident analysis, controlled rollout, and rollback require known inputs.
- Consequence: upgrades are explicit, compatibility-tested, and canaried.

## D-009 — Operator-controlled pilot first

- Status: Accepted
- Date: 2026-07-19
- Decision: initial provisioning is restricted to platform admins and an explicit tenant allowlist.
- Rationale: OpenClaw introduces infrastructure cost, powerful tools, and new operational risk.
- Consequence: pilot tenants have quotas, budgets, kill switches, and approval for consequential actions; self-service comes later.

## D-010 — Shared edge is a trusted pilot component

- Status: Accepted for pilot
- Date: 2026-07-19
- Decision: for the pilot, use one hardened shared edge that the worker attaches to isolated tenant ingress networks.
- Rationale: this preserves the existing OCTW routing model while allowing the first pilot to validate authorization, WebSocket behavior, wake-up, and network isolation.
- Consequence: tenant-runtime compromise must remain contained, but edge, worker, Docker-host, or signing-key compromise is a platform-wide incident. General availability requires an explicit threat-model review that accepts this blast radius or replaces the design with stronger per-tenant ingress.
- Specification: `SPEC.md` §2.1 and §8.

## D-011 — Idempotency applies to every mutation

- Status: Accepted
- Date: 2026-07-19
- Decision: every mutating platform request requires an idempotency key scoped by service identity, route, semantic action, and key; durable database uniqueness is the correctness mechanism.
- Rationale: retries and concurrent delivery affect lifecycle, secret, retry, cancellation, and deletion operations, not only creation.
- Consequence: OCTW retains canonical request hashes and original results for 30 days, returns the original response for equivalent retries, and rejects conflicting key reuse.
- Specification: `SPEC.md` §5.

## D-012 — Opaque staged secret references

- Status: Accepted
- Date: 2026-07-19
- Decision: AriCRM binds allowlisted semantic slots to opaque, versioned `octw-secret://` references; values enter OCTW only through write-only staging and rotation endpoints.
- Rationale: callers must not control environment-variable names or retrieve runtime secrets, while provisioning still needs a deterministic contract for required credentials.
- Consequence: staged secrets expire after 24 hours if unbound; profiles/templates declare permitted slots; rotation creates a new version and a reload/restart operation.
- Specification: `SPEC.md` §9.1.

## D-013 — Pilot retention, reuse cooldown, and recovery objectives

- Status: Accepted for pilot
- Date: 2026-07-19
- Decision: use the pilot defaults in `SPEC.md` §3 and §10.1: seven-day external-reference reuse cooldown; 30-day idempotency/callback retention; 90-day operations/log retention; 365-day sanitized audit/tombstone retention; control-plane RPO 15 minutes/RTO 4 hours; tenant-workspace RPO 24 hours/RTO 8 hours.
- Rationale: deletion, retries, incident investigation, privacy, backup expiry, and recovery tests need explicit time bounds before implementation.
- Consequence: these values are approved pilot policy by the project owner. General availability still requires explicit reapproval after restore, deletion, privacy, and operations evidence exists.
- Specification: `SPEC.md` §3, §10.1, and §13.
