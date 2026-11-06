# Delivery roadmap

This is a prototype roadmap, not a release commitment. All demonstrations use fictional data.

| Milestone | Implemented | Exit criteria / remaining work |
| --- | --- | --- |
| 1. Clear product presentation | Versioned identity, capability matrix, actual showcase capture, architecture and reproducible commands | Verify GitHub rendering after the branch is pushed |
| 2. Persistent execution backend | Local deterministic core and CLI only | FastAPI validation, migrations, durable task states and events, idempotency, bounded retries, cancellation and approval tied to a stored plan; integration tests |
| 3. Connected operator workspace | Separate read-only operations showcase | Responsive accessible task submission, approval and execution history connected to the backend; browser tests |
| 4. Controlled AI planning | No LLM provider | Provider abstraction, schema validation, tool scoping, untrusted-content boundaries, traceable usage and enforced budgets; fake-provider contract tests plus opt-in live validation |
| 5. End-to-end support pilot | Independent ticket-triage demo | Request → persisted plan → human approval → permitted local action → stored result → dashboard history; reproducible integration test |
| 6. SaaS foundation | Not implemented | Authentication, RBAC, tenant isolation tests, secret configuration, usage metering, entitlement and billing abstractions; deployment and recovery validation |
| 7. Commercial validation | Pilot invitation only | Agree customer scope, data policy, acceptance criteria, costs and ownership; validate pricing before enabling any charges |

## Next implementation increment

Build and test a persistent support-request API around the existing deterministic core. Keep provider calls and external actions disabled by default. Approval must bind to the exact stored task and plan; the current CLI boolean is not authenticated authorization. Deliver the connected dashboard after the task lifecycle is stable.

## Commercial hypotheses

Starter R$99/month, Professional R$299/month, Business R$999/month and Enterprise custom are unvalidated hypotheses. No subscriptions, live charges, customer outcomes or service-level commitments are active.

## Ownership and licensing

No license grant is declared. Confirm contribution ownership and choose the public/proprietary boundary before distributing commercial software. Future dependency adoption needs a license inventory and vulnerability review. Never publish customer data or private integrations.
