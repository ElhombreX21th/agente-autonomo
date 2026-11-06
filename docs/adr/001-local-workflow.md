# ADR 001: A persistent single-operator workflow before SaaS

Status: accepted for the local development increment.

## Context

The existing core is deterministic, uses three bounded local tools, and has no remote side effects. The existing approval boolean does not identify a stored task. Adding external actions or billing before durable lifecycle semantics would obscure authorization and recovery behavior.

## Decision

Keep the standard-library core and CLI intact. Add FastAPI/Pydantic validation, a small SQLite repository and a same-origin HTML/CSS/JavaScript workspace. SQLite avoids a mandatory database server while supporting transactional task results. A future PostgreSQL/SQLAlchemy/Alembic migration and Next.js application are separate increments, after authentication and tenancy contracts are defined. The browser UI needs no asset build or third-party scripts.

Creation is idempotent per client key. A conflicting payload returns 409. A plan hash binds approval to one immutable task and selected tool; it is an integrity token, not authentication. An immediate database write transaction serializes approval and cancellation. These synchronous tools have bounded 5,000-character inputs and no external side effects; execution, result and event records commit together. Replayed approval returns the committed result without running again. A tool exception yields a stored failed state without exposing exception contents. Failed tasks require a new reviewed request. A process crash rolls back the transaction; no distributed exactly-once guarantee is claimed.

States: approval_required → completed / failed / cancelled. Only pending tasks can be cancelled. There is no worker queue, in-flight interruption, time limit, automatic retry or mutable plan. Adding I/O-bound tools requires a different worker/lease/outbox design and scoped authorization first.

## Security and operational consequences

One local operator, fictional data, loopback bind only. Trusted-host checks and same-origin write checks address browser-origin attacks; neither supplies user authentication. No permissive CORS configuration. No outbound tools, API keys, billing or LLM. User content is rendered through textContent, not HTML. Database and virtual environments are ignored by Git. Local events are application-managed records, not cryptographically tamper-proof audit storage. A client with local access can approve tasks; do not deploy this service to shared or public networks.

The schema uses CREATE TABLE IF NOT EXISTS for version 1 only; controlled migration tooling, backup/restore procedures, tenant isolation, retention, authentication, rate limits and security review are pending. Dependency versions are frozen for repeatable development, not proof of freedom from vulnerabilities.
