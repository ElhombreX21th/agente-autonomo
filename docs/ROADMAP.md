# Delivery roadmap

This is a prototype roadmap, not a release commitment. All demonstrations use fictional data.

| Milestone | Implemented | Exit criteria / remaining work |
| --- | --- | --- |
| 1. Clear product presentation | Versioned identity, capability matrix, actual showcase capture, architecture and reproducible commands | Verify GitHub rendering after the branch is pushed |
| 2. Persistent execution backend | Local deterministic core, CLI, FastAPI + SQLite task/result/event storage, idempotency and plan-bound approval | Remaining: migrations, authenticated approvals, bounded retries/timeouts for future I/O tools and worker lifecycle |
| 3. Connected operator workspace | Connected local task workspace plus separate operations showcase | Implemented submission, approval, result, export, history, pending cancellation; browser smoke tested. Remaining: broader accessibility audit and production UI architecture |
| 4. Controlled AI planning | No LLM provider | Provider abstraction, schema validation, tool scoping, untrusted-content boundaries, traceable usage and enforced budgets; fake-provider contract tests plus opt-in live validation |
| 5. End-to-end support pilot | Reproducible deterministic support-request lifecycle | Verified request → stored plan → approval → local keyword classification → result → history/export. AI interpretation is not implemented. |
| 6. SaaS foundation | Not implemented | Authentication, RBAC, tenant isolation tests, secret configuration, usage metering, entitlement and billing abstractions; deployment and recovery validation |
| 7. Commercial validation | Pilot invitation only | Agree customer scope, data policy, acceptance criteria, costs and ownership; validate pricing before enabling any charges |

## Next implementation increment

Add authenticated operator identity and authorization before any shared deployment. Define tenant scope and migration strategy, then introduce a configurable LLM provider with schema validation, explicit budgets and adversarial input tests. Keep external actions disabled until connector authorization and recovery semantics are tested.

## Commercial hypotheses

Starter R$99/month, Professional R$299/month, Business R$999/month and Enterprise custom are unvalidated hypotheses. No subscriptions, live charges, customer outcomes or service-level commitments are active.

## Ownership and licensing

No license grant is declared. Confirm contribution ownership and choose the public/proprietary boundary before distributing commercial software. Future dependency adoption needs a license inventory and vulnerability review. Never publish customer data or private integrations.
